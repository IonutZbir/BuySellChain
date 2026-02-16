from datetime import datetime
from flask import Blueprint, jsonify, request,current_app

from app.models.models import AssetType
from app.services.asset_services import AssetService
from flask_jwt_extended import jwt_required,get_current_user

from app.services.jsend import jsend_response
api_assets = Blueprint("api_assets", __name__)


# Questo file comunica direttamente con Asset Serivices, dove sono definite tutte le operazioni che si possono fare con gli asset.

@api_assets.route("/assets", methods=["POST"])
@jwt_required()
def post_assets():
    data = request.json
    owner_id = get_current_user()["id"]
    title = data.get("title")
    descr = data.get("descr")
    asset_type = data.get("type")
    size = data.get("size")
    price = data.get("price")
    locat = data.get("locat")

    
    # Validate required fields
    if not all([title, descr, asset_type, size, price, locat]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        asset_type = AssetType.from_value(type)
    except (ValueError):
        return jsonify({"error": "Invalid asset type"}), 400
    
    # Validate data types and values
    try:
        size = float(size)
        price = float(price)
        if size <= 0 or price <= 0:
            return jsonify({"error": "Size and price must be positive numbers"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Size and price must be numeric"}), 400
    
    result = AssetService.create_asset(owner_id, title, descr, asset_type, size, price, locat)
    
    return jsend_response("success", code=200), 200 if result else jsend_response("fail", code=400)


@api_assets.route("/assets", methods=["GET"])
# @jwt_required()
def get_assets():
    result = AssetService.list_all_assets()
    
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    return jsend_response("success", data=result.get("assets"))


@api_assets.route("/assets/<string:asset_id>", methods=["GET"])
def get_asset(asset_id):
    result = AssetService.get_asset(asset_id)
    
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    asset_data = result.get("data", {})
    return jsend_response("success", data={"id": asset_id, "data": asset_data})


@api_assets.route("/assets/user", methods=["GET"])
@jwt_required()
def get_assets_by_user():
    user_id = get_current_user()["id"]
    
    result = AssetService.get_assets_by_user(user_id)
    
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    return jsend_response("success", data={"assets": result.get("assets")})
