from datetime import datetime
from flask import Blueprint, jsonify, request,current_app

from app.services.guile_services import GuileService
from hashlib import sha256
from uuid import uuid4
from flask_jwt_extended import jwt_required, get_jwt_identity,get_current_user
api_assets = Blueprint("api_assets", __name__)


# aggiungere mappatura per asset, ad esempio:
@api_assets.route("/assets/<string:asset_id>", methods=["GET"])
def get_asset(asset_id):

    print(f"Received request for asset with ID: {asset_id}")  # Debug print
    result = GuileService.GetKV(Class="Assets", key=str(asset_id))
    print("Result from GetKV:", result)  # Debug print

    ans = result.get('answer')

    if ans != False:
        asset_data = result.get("answer", {})
        print(f"Asset data for ID {asset_id}:", asset_data)  # Debug print
        return jsonify({"id": asset_id, "data": asset_data}), 200
    else:
        print(f"Asset with ID {asset_id} not found.")  # Debug print
        return jsonify({"error": "Asset not found"}), 404
    
# id+francosalvucci@yahoo.com -> hash()

#user_id = nome+cognome+email+id(da postgres)

@api_assets.route("/assets/user", methods=["GET"])
@jwt_required()
def get_assets_by_user():

    user_id = get_current_user()["id"]
    #user_id = "b30b2e7ae1276ff52843e6e58524ef40a08861714a444ae1a45ed6bc445e3c68" # da rimuovere, serve solo per testare senza autenticazione
    print(f"Received request for assets of user with ID: {user_id}")  # Debug print

    result = GuileService.GetKeys(Class="Assets")

    print("Result from GetKeys (asset-user):", result)  # Debug print
    answer = result.get("answer", {})
    keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]

    print("Extracted keys list:", keys_list)  # Debug print
    user_assets = []
    for key in keys_list:

        print(f"Asset key: {key}")  # Debug print
        
        result_asset = GuileService.GetKV(Class="Assets", key=str(key))
        asset_data = result_asset.get("answer", {}).get("value", {})
        if asset_data.get("ownerId") == user_id:
            user_assets.append({"id": key, "data": asset_data})

        print(f"Asset data for key {key}:", asset_data)  # Debug print
    return jsonify({"assets": user_assets}), 200 if "error" not in result else 400

@api_assets.route("/assets", methods=["GET"])
def list_assets():

    result = GuileService.GetKeys(
        Class="Assets",
    )
    print("Result from GetKeys:", result)  # Debug print
    answer = result.get("answer", {})
    keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
    print("Extracted keys list:", keys_list)  # Debug print
    for key in keys_list:
        print(f"Asset key: {key}")  # Debug print
        
        result_asset = GuileService.GetKV(Class="Assets", key=str(key))
        
        print(f"Asset data for key {key}:", result_asset)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400


@api_assets.route("/assets", methods=["POST"])
@jwt_required()
def create_asset():
    data = request.json
    # desc = data.description
    ###
    # ownerId = get_jwt_identity()["id"]
    # Metadati da Frontend:
    # {ownerId,title, descr, typr, size, price, locat, }
    #currentAuctionId èrima volta NULL, ppi modifica dopo la creazione dell'asta, quando si sa a quale asta è associato l'asset
    #createdAt = tempo corrente datetime.now() in formato timestamp
    # stauts all'inizio "active", poi "locked" durante asta, poii "transf"
    # key = hash value + Nonce (true random generator)/UUID (mo vediamo)
    ###
    ownerId = get_current_user()["id"]
    # type = "villa" # da rimuovere, serve solo per testare senza autenticazione
    # size = 100 # da rimuovere, serve solo per testare senza autenticazione
    # price = 100000 # da rimuovere, serve solo per testare senza autenticazione
    # locat = "Roma" # da rimuovere, serve solo per testare
    # descr = "Casa grande a Roma" # da rimuovere, serve solo per testare senza autenticazione
    # title = "Casa a Roma" # da rimuovere, serve solo per testare senza autenticazione

    value = {
        "ownerId": ownerId,
        "title": data.get("title"),
        "descr": data.get("descr"),
        "type": data.get("type"),
        "size": data.get("size"),
        "price": data.get("price"),
        "locat": data.get("locat"),
        "currentAuctionId": None,
        "createdAt": datetime.now().timestamp(),
        "status": "active",
    }

    # value = {
    #     "ownerId": ownerId,
    #     "title": title,
    #     "descr": descr,
    #     "type": type,
    #     "size": size,
    #     "price": price,
    #     "locat": locat,
    #     "currentAuctionId": None,
    #     "createdAt": datetime.now().timestamp(),
    #     "status": "active",
    # }

    key = sha256(str(value).encode() + str(uuid4()).encode()).hexdigest()  # Genera un hash unico per l'asset
    current_app.logger.debug(f"Creata Asset da Frontend: {key}")  # Debug print
    print(f"Creata Asset da Frontend: {key}")
    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Assets", key=key, value=value
    )
    print("Result from AddKV:", result)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400
