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
#jwt_required() #--- da rimettere quando si toglie la parte hardcoded per testare senza autenticazione
def create_bid():
    #route che crea una nuova offerta tramite POST /bids
    data = request.json
    #bidder_id = get_current_user()["id"] #--- da rimettere quando si toglie la parte hardcoded per testare senza autenticazione
    bidder_id = 2 #--- hardcoded per testare senza autenticazione, da togliere quando si rimettono i jwt
    #auction_id = data.get("auction_id")
    auction_id = "abb45f25f607d504ada4c39d54156441618ca2c42016af3aea69c299a4cd8a8d" #--- hardcoded per testare senza autenticazione, da togliere quando si rimettono i jwt
    #amount = data.get("amount")
    amount = 100000 #--- hardcoded per testare senza autenticazione, da togliere quando si rimettono i jwt

    if not all([auction_id, amount]):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"error": "Amount must be a positive number"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be numeric"}), 400
    
    result = BidService.create_bid(auction_id, bidder_id, amount)
    if not result.get("success"):
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
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

@api_bids.route("/bids/user/<int:user_id>", methods=["GET"])
# ritorna tutte le offerte fatte da un utente, con i relativi dati (asta, asset, ecc) -
#  da vedere se farla fare ad admin o a utente stesso (con controllo che user_id corrisponda a quello del token)
def list_bids_by_user(user_id):
    result = BidService.list_bids_by_user(user_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data=result.get("bids"))

@api_bids.route("/bids/<string:bid_id>", methods=["GET"])
# route che ritorna i dati di un'offerta specifica, dato il suo ID (key)
def get_bid_by_id(bid_id):
    result = BidService.get_bid_by_id(bid_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    bid_data = result.get("bid_data", {})
    return jsend_response("success", data={"bid_data_from_id": bid_data})

@api_bids.route("/bids/<string:bid_id>/validate", methods=["POST"])
# route che permette di validare un'offerta, accettandola o rifiutandola, con eventuale motivazione (solo per admin o venditore, con controllo che user_id corrisponda a quello del token)
def validate_bid(bid_id):
    data = request.json
    #status = data.get("status") #accepted o rejected
    #reason = data.get("reason") #opzionale, da mettere se rejected, per motivare il rifiuto (es: offerta troppo bassa, ecc)
    
    result = BidService.validate_bid(bid_id)
    if not result.get("success"):
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    return jsend_response("success", code=200)