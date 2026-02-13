from flask import Blueprint, jsonify, request

from app.services.guile_services import GuileService

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
        
        result_asset = GuileService.GetKV(Class="Asset", key=str(key))
        
        print(f"Asset data for key {key}:", result_asset)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400


@api_assets.route("/assets", methods=["POST"])
# @jwt_required()
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

    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Assets", key=data.get("key"), value=data.get("value")
    )
    print("Result from AddKV:", result)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400
