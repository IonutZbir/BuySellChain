from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_current_user

from app.models.models import AssetType, Messages, LogType
from app.services.asset_services import AssetService
from app.services.log_services import LogService
from app.services.jsend import jsend_response

api_assets = Blueprint("api_assets", __name__)


# Questo file comunica direttamente con Asset Serivices, dove sono definite tutte le operazioni che si possono fare con gli asset.


@api_assets.route("/assets", methods=["POST"])
@jwt_required()
def post_assets():
    user = get_current_user()
    owner_id = user["id"]

    role = user.get("role")
    if role != "seller":
        LogService.record_log(message=Messages.PREFIX_ACCESSO_NON_AUTORIZZATO.value + " /assets", level=LogType.ALERT, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="POST")
        return jsonify({"error": "Accesso negato"}), 403

    title = request.form.get("title")
    descr = request.form.get("descr")
    asset_type = request.form.get("type")
    size = request.form.get("size")
    price = request.form.get("price")
    locat = request.form.get("locat")

    current_app.logger.debug(f"Received form data: {request.form}")

    if not all([title, descr, asset_type, size, price, locat]):
        return jsonify({"error": "Missing required text fields"}), 400

    if "picture" not in request.files:
        return jsonify({"error": "Missing asset image"}), 400

    picture = request.files["picture"]

    if picture.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        asset_type = AssetType.from_value(asset_type)
        current_app.logger.debug(f"Validate asset type: {asset_type}")
    except ValueError:
        return jsonify({"error": "Invalid asset type"}), 400

    try:
        size = float(size)
        price = float(price)
        if size <= 0 or price <= 0:
            return jsonify({"error": "Size and price must be positive numbers"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Size and price must be numeric"}), 400

    result = AssetService.create_asset(
        owner_id, title, descr, asset_type, size, price, locat, picture
    )
    if result:
        LogService.record_log(message=Messages.REGISTRAZIONE_ASSET_BL, level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="POST")

    return jsend_response("success", code=200) if result else jsend_response("fail", code=400)


@api_assets.route("/assets", methods=["GET"])
@jwt_required()
def get_assets():
    result = AssetService.list_all_assets()

    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)

    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)

    return jsend_response("success", data=result.get("assets"))


@api_assets.route("/assets/<string:asset_id>", methods=["GET"])
@jwt_required()
def get_asset(asset_id):
    result = AssetService.get_asset(asset_id)

    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)

    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)

    asset_data = result.get("data", {})
    return jsend_response("success", data=asset_data)


@api_assets.route("/assets/user", methods=["GET"])
@jwt_required()
def get_assets_by_user():
    user_id = get_current_user()["id"]

    result = AssetService.get_assets_by_user(user_id)

    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)

    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    LogService.record_log(message=f"Visione degli asset di utente {user_id}", level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="GET")

    return jsend_response("success", data={"assets": result.get("assets")})
