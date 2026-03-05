from datetime import datetime
from flask import Blueprint, jsonify, request
from hashlib import sha256
from uuid import uuid4
from flask_jwt_extended import jwt_required, get_jwt_identity,get_current_user
from app.services.guile_services import GuileService
from app.services.bid_services import BidService
from app.services.jsend import jsend_response

api_bids = Blueprint("api_bids", __name__)

@api_bids.route("/bids", methods=["POST"])
@jwt_required()
def create_bid():
    #route che crea una nuova offerta tramite POST /bids
    data = request.json
    bidder_id = get_current_user()["id"]
    auction_id = data.get("auction_id")
    amount = data.get("amount")
    
    if not all([auction_id, amount]):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"error": "Amount must be a positive number"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be numeric"}), 400

    result = BidService.create_bid(auction_id, bidder_id, amount)

    print(f"Bid creation result: {result}")  # Debug print
    if not result.get("success"):
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    else:
        if not result.get("validate_success"):
            return jsend_response("fail", data={"error": result.get("Bid_status_reason")}, code=400)
    
    return jsend_response("success", code=200)

# vedere se farla fare ad admin
@api_bids.route("/bids", methods=["GET"])
# route che ritorna tutte le offerte, con i relativi dati (asta, asset, ecc) -
#  da vedere se farla fare ad admin o a utente stesso (con controllo che user_id corrisponda a quello del token)
def list_bids():
    result = BidService.list_all_bids()
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data=result.get("bids"))

@api_bids.route("/bids/user/", methods=["GET"])
# ritorna tutte le offerte fatte da un utente, con i relativi dati (asta, asset, ecc) -
#  da vedere se farla fare ad admin o a utente stesso (con controllo che user_id corrisponda a quello del token)
@jwt_required()
def list_bids_by_user():
    user_id = get_current_user()["id"]
    result = BidService.list_bids_by_user(user_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data=result.get("bids"))

@api_bids.route("/bids/latest/<auction_id>", methods=["GET"])
@jwt_required()
def get_latest_bid_for_auction(auction_id):
    bidderId = get_current_user()["id"]
    result = BidService.get_latest_bid_for_auction(auction_id,bidderId)
    
    if not result.get("success"):
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    
    return jsend_response("success", data={"latest_bid": result.get("latest_bid")})