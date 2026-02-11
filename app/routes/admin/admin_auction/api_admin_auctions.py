from flask import Blueprint, jsonify, request

from app.services.guile_services import GuileService

api_admin_auctions = Blueprint("api_admin_auctions", __name__)


@api_admin_auctions.route("/history/auctions/<string:key>", methods=["GET"])
def get_history(key):
    """
    GET /admin/history/{key} Endpoint di auditing che espone la cronologia immutabile
    di una specifica chiave (asset o asta), invocando la primitiva GetKeyHistory del
    chaincode.
    """
    result = GuileService.GetKeyHistory(Class="Auctions", key=key)
    return jsonify(result), 200 if "error" not in result else 400