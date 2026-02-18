from unittest import result
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from uuid import uuid4
from datetime import datetime
from app.services.guile_services import GuileService
from hashlib import sha256
from app.services.auction_services import AuctionService
from app.services.jsend import jsend_response
api_auctions = Blueprint("api_auctions", __name__)


###
# offerte per utente
#imponiamo tempo limite per asta (diviso in finestre temporale)
#poi si aggiurango i dati tipo higBidAmout, higBdId, etc.., minIncrement
#durante l'agiroanemnto status dicenta LOCKED,
#allo scoccare di goni finestra temporale, l'utente può fare al più UNA sola offerta
# y=kx, con y=asta e x=tempo, con k coefficiente da definire (esempio 0.1, 0.2, etc) - da vedere se è meglio fare così o imporre un incremento minimo fisso (esempio 10 euro)
###

@api_auctions.route("/auctions", methods=["POST"])
@jwt_required()
def create_auction():
    data = request.json
    user = get_current_user()
    sellerId = user.get("id")
    # highBidId = None
    # highBidAmount = None
    # bidCount = 0
    # status = "active"
    assetId = data.get("assetId")
    startTime = data.get("startTime")
    endTime = data.get("endTime")
    startingPrice = data.get("startingPrice")
    minIncr = data.get("minIncr")
    
    # Validate required fields
    if not all([startTime, endTime, startingPrice, minIncr]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate data types and values
    try:
        startTime = datetime.fromisoformat(startTime)
        endTime = datetime.fromisoformat(endTime)
        startingPrice = float(startingPrice)
        minIncr = float(minIncr)
        if startingPrice <= 0 or minIncr <= 0:
            return jsonify({"error": "Starting price and minimum increment must be positive numbers"}), 400
        # facciamo che min_incr sia almeno il 10% del prezzo di partenza, per evitare aste con incrementi troppo bassi
        if minIncr < 0.1 * startingPrice:
            return jsonify({"error": "Minimum increment must be at least 10% of the starting price"}), 400
        if endTime <= startTime:
            return jsonify({"error": "End time must be after start time"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid data types for auction fields"}), 400
    
    result = AuctionService.create_auction(assetId, sellerId, startTime, endTime, startingPrice, minIncr)
    current_app.logger.info(f"Result from AssetService.create_asset: {result}")  # Debug print

    print("[INFO] Auction creation result:", result)  # Debug print
    return jsend_response("success", code=200) if result else jsend_response("fail", code=400)


@api_auctions.route("/auctions", methods=["GET"])
def list_auctions():
    result = AuctionService.list_all_auctions()
    
    # se asta attiva, inviare al frontend anche il nome dell owner e il nome dell'asset, descrzione asset
    
    
    current_app.logger.debug(f"Result from AuctionService.get_assets_by_user: {result}")  # Debug print

    
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    return jsend_response("success", data={"auctions": result.get("auctions")})


@api_auctions.route("/auctions/status/<string:status>", methods=["GET"])
def list_auctions_by_status(status):
    result = AuctionService.get_auction_by_status(status)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data={"auctions": result.get("auctions")})

# /auctions/user/{id}/status/{id}

@api_auctions.route("/auctions/<string:auction_id>", methods=["GET"])
def get_auction_by_id(auction_id):
    result = AuctionService.get_auction(auction_id)
    
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    
    asset_data = result.get("auction_data", {})
    return jsend_response("success", data=asset_data)


@api_auctions.route("/auctions/<string:auction_id>", methods=["DELETE"])
#@jwt_required()
def delete_auction(auction_id):
    #user = get_current_user()
    #sellerId = user.get("id")
    sellerId = "23e83c13c39ac78c4aee0ae0a3381d3656a95258d1efc44e0c9e9126fdb80f0d"  # Placeholder, replace with actual seller ID from JWT
    result = AuctionService.cancel_auction(auction_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore durante l'eliminazione dell'asta"}, code=500)
    return jsend_response("success", code=200)

#fare funzione che prende immagini da cartelle su webserver, con nome corrispondente all'id dell'asta, e le aggiunge agli oggetti delle aste