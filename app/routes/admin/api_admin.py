from flask import Blueprint, jsonify, request

from app.services.guile_services import GuileService

api_admin = Blueprint("api_admin", __name__)


# aggiungere mappatura per asset, ad esempio:
@api_admin.route("/users", methods=["GET"])
def get_users():
    """
    GET /admin/users Restituisce l’elenco completo degli utenti registrati nel database off-
    chain e il loro stato (attivo/sospeso), per permettere all’amministratore di gestire le
    utenze.
    """
    # PLACEHOLDER: Simulazione di una risposta con dati fittizi
    users = [
        {"username": "user1", "status": "active"},
        {"username": "user2", "status": "suspended"},
        {"username": "user3", "status": "active"},
    ]
    return jsonify({"users": users}), 200


@api_admin.route("/stats", methods=["GET"])
def get_stats():
    """
    GET /admin/stats Fornisce metriche aggregate del sistema, come il numero totale di
    aste concluse, il volume delle transazioni e il numero di asset registrati, invocando
    GetNumKeys sulle diverse classi.
    """
    # PLACEHOLDER: Simulazione di una risposta con dati fittizi
    total_auctions = GuileService.GetNumKeys(Class="Auctions")
    total_assets = GuileService.GetNumKeys(Class="Assets")
    total_bids = GuileService.GetNumKeys(Class="Bids")
    print(f"Total auctions: {total_auctions}, Total assets: {total_assets}, Total bids: {total_bids}")  # Debug print
    stats = {
        "total_auctions": total_auctions.get("answer", {}).get("numkeys", 0),
        "total_volume": 50000,
        "total_assets": total_assets.get("answer", {}).get("numkeys", 0),
        "total_bids": total_bids.get("answer", {}).get("numkeys", 0),
    }
    return jsonify({"stats": stats}), 200
    
