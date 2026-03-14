import os

from flask import Blueprint, current_app
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy import select

from app import db
from app.models.models import User
from app.services.auction_services import AuctionService
from app.services.guile_services import GuileService
from app.services.jsend import jsend_response

api_admin = Blueprint("api_admin", __name__)


def _ensure_admin():
    user = get_current_user()
    if not user or user.get("role") != "admin":
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
    _, error = _ensure_admin()
    if error:
        return error

    query = select(User).order_by(User.created_at.desc())
    users_db = db.session.execute(query).scalars().all()

    users = []
    for user in users_db:
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

    return jsend_response("success", data={"users": users}, code=200)


@api_admin.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """
    GET /admin/stats Fornisce metriche aggregate del sistema, come il numero totale di
    aste concluse, il volume delle transazioni e il numero di asset registrati, invocando
    GetNumKeys sulle diverse classi.
    """
    _, error = _ensure_admin()
    if error:
        return error

    total_auctions = GuileService.GetNumKeys(Class="Auctions")
    total_assets = GuileService.GetNumKeys(Class="Assets")
    total_bids = GuileService.GetNumKeys(Class="Bids")

    auctions_count = _safe_numkeys(total_auctions)
    assets_count = _safe_numkeys(total_assets)
    bids_count = _safe_numkeys(total_bids)

    all_auctions_result = AuctionService.list_all_auctions()
    total_volume = 0.0
    active_auctions = 0
    closed_auctions = 0

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
        "total_users": len(db.session.execute(select(User.blockChainId)).all()),
        "total_volume": round(total_volume, 2),
    }

    return jsend_response("success", data={"stats": stats}, code=200)


@api_admin.route("/auctions", methods=["GET"])
@jwt_required()
def get_admin_auctions():
    _, error = _ensure_admin()
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

    log_path = os.path.join("logs", "app.log")
    if not os.path.exists(log_path):
        return jsend_response("success", data={"logs": []}, code=200)

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
            lines = [line.rstrip("\n") for line in log_file if line.strip()]
    except OSError as exc:
        current_app.logger.error("Errore nella lettura del file di log: %s", exc)
        return jsend_response("error", message="Errore nella lettura dei log", code=500)

    tail_lines = lines[-120:]
    logs = []
    for index, line in enumerate(tail_lines, 1):
        logs.append({"id": index, "message": line})

    return jsend_response("success", data={"logs": logs}, code=200)

