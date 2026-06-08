from flask import Blueprint, current_app, request
from flask_jwt_extended import get_current_user, jwt_required

from app.models.models import LogType, Messages
from app.services.auction_services import AuctionService
from app.services.guile_services import GuileService
from app.services.jsend import jsend_response
from app.services.log_services import LogService
from app.services.user_services import UserService

api_admin = Blueprint("api_admin", __name__)


def _ensure_admin(endpoint=""):
    user = get_current_user()
    if not user or user.get("role") != "admin":
        LogService.record_log(message=Messages.PREFIX_ACCESSO_NON_AUTORIZZATO + endpoint, level=LogType.ALERT, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="GET")
        return None, jsend_response("fail", data={"error": "Accesso riservato agli amministratori"}, code=403)
    return user, None


def _safe_numkeys(result):
    if isinstance(result, dict):
        return result.get("answer", {}).get("numkeys", 0)
    return 0


# aggiungere mappatura per asset, ad esempio:
@api_admin.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    """
    GET /admin/users Restituisce l'elenco completo degli utenti registrati nel database off-
    chain e il loro stato (attivo/sospeso), per permettere all'amministratore di gestire le
    utenze.
    """
    endpoint = "/users"
    _, error = _ensure_admin(endpoint)
    if error:
        return error

    users_result = UserService.list_users()
    if not users_result.get("success"):
        return jsend_response("fail", data={"error": users_result.get("error", "Errore nel recupero utenti")}, code=500)

    users = []
    for user in users_result.get("users", []):
        users.append(
            {
                "id": user.blockChainId,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.lastLoginAt.isoformat() if user.lastLoginAt else None,
            }
        )
    
    #LogService.record_log(message=Messages.PREFIX_GET_ADMIN_ROUTE.value + "/users", level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="GET")
    return jsend_response("success", data={"users": users}, code=200)


@api_admin.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """
    GET /admin/stats Fornisce metriche aggregate del sistema, come il numero totale di
    aste concluse, il volume delle transazioni e il numero di asset registrati, invocando
    GetNumKeys sulle diverse classi.
    """
    endpoint = "/stats"
    _, error = _ensure_admin(endpoint)
    if error:
        return error

    total_auctions = GuileService.GetNumKeys(Class="Auctions")
    total_assets = GuileService.GetNumKeys(Class="Assets")
    total_bids = GuileService.GetNumKeys(Class="Bids")
    users_result = UserService.list_users()

    auctions_count = _safe_numkeys(total_auctions)
    assets_count = _safe_numkeys(total_assets)
    bids_count = _safe_numkeys(total_bids)

    all_auctions_result = AuctionService.list_all_auctions()
    total_volume = 0.0
    active_auctions = 0
    closed_auctions = 0


    # qua total_volume prende high_bid_amount, ma per tutta l'asta il valore è None, 
    # viene aggiornato quando l'asta va in locked, funziona?
    if all_auctions_result.get("success"):
        for auction in all_auctions_result.get("auctions", []):
            value = auction.get("value", {})
            total_volume += float(value.get("high_bid_amount") or 0) 
            status = (value.get("status") or "").lower()
            if status == "active":
                active_auctions += 1
            if status == "closed":
                closed_auctions += 1

    stats = {
        "total_auctions": auctions_count,
        "total_assets": assets_count,
        "total_bids": bids_count,
        "active_auctions": active_auctions,
        "closed_auctions": closed_auctions,
        "total_users": len(users_result.get("users", [])) if users_result.get("success") else 0,
        "total_volume": round(total_volume, 2),
    }

    return jsend_response("success", data={"stats": stats}, code=200)


@api_admin.route("/auctions", methods=["GET"])
@jwt_required()
def get_admin_auctions():
    endpoint = "/auctions"
    _, error = _ensure_admin(endpoint)
    if error:
        return error

    result = AuctionService.list_all_auctions()
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error", "Impossibile recuperare le aste")}, code=404)

    auctions = []
    for auction in result.get("auctions", []):
        value = auction.get("value", {})
        auctions.append(
            {
                "id": value.get("id"),
                "asset_id": value.get("asset_id"),
                "seller_id": value.get("seller_id"),
                "status": value.get("status"),
                "start_time": value.get("start_time"),
                "end_time": value.get("end_time"),
                "starting_price": value.get("starting_price"),
                "high_bid_amount": value.get("high_bid_amount"),
                "bid_count": value.get("bid_count"),
            }
        )

    return jsend_response("success", data={"auctions": auctions}, code=200)


@api_admin.route("/logs", methods=["GET"])
@jwt_required()
def get_admin_logs():
    _, error = _ensure_admin()
    if error:
        return error

    result = LogService.list_logs(limit=120)
    if not result.get("success"):
        current_app.logger.error("Errore nella lettura dei log da blockchain: %s", result.get("error"))
        return jsend_response("error", message="Errore nella lettura dei log", code=500)

    LogService.record_log(message=Messages.PREFIX_GET_ADMIN_ROUTE.value + "/logs", level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="GET")

    return jsend_response("success", data={"logs": result.get("logs", [])}, code=200)