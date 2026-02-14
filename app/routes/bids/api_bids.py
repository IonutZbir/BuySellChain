from datetime import datetime
from flask import Blueprint, jsonify, request
from hashlib import sha256
from uuid import uuid4
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.guile_services import GuileService


api_bids = Blueprint("api_bids", __name__)

@api_bids.route("/bids", methods=["POST"])
#@jwt_required() --- da rimettere quando si toglie la parte hardcoded per testare senza autenticazione
def create_bid():
    #route che crea una nuova offerta tramite POST /bids
    data = request.json

    ### Metadati da Frontend:
    # {auctionId, bidderId, amount, }
    # TIMESTAMPT calcolato qui
    # validare amount >= basePrice+increment (da fare lato frontend, ma poi anche qui per sicurezza)
    # - se mgarriore uguale status accettato, altrimenti stauts rigettato (con Reason)
    #validare anche che l'asta sia ancora attiva (non scaduta, non conclusa, ecc)
    #- se utente cerca di fare Bid per asta non attiva, rigettare con Reason "Auction not active"

    bidderId = 12 # da rimuovere, serve solo per testare senza autenticazione
    auctionId = 15 # da rimuovere, serve solo per testare senza autenticazione
    amount = 150 # da rimuovere, serve solo per testare senza autenticazione
    timestamp = datetime.now().isoformat() # calcolato qui, non da frontend
    status = "rejected" # da calcolare
    reason = "amount too low" # da calcolare

    value = {
        "auctionId": auctionId,
        "bidderId": bidderId,
        "amount": amount,
        "timestamp": timestamp,
        "status": status,
        "reason": reason
    }
    key = sha256(str(value).encode() + str(uuid4()).encode()).hexdigest()  # Genera un hash unico per il bid
    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Bids", key=key, value=value
    )
    print("Result from AddKV:", result)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400

# vedere se farla fare ad admin
@api_bids.route("/bids", methods=["GET"])
# route che ritorna tutte le offerte, con i relativi dati (asta, asset, ecc) -
#  da vedere se farla fare ad admin o a utente stesso (con controllo che user_id corrisponda a quello del token)
def list_bids():
    result = GuileService.GetKeys(
        Class="Bids",
    )
    print("Result from GetKeys:", result)  # Debug print
    answer = result.get("answer", {})
    keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
    print("Extracted keys list:", keys_list)  # Debug print
    print("-"*100)
    print("# keys:", len(keys_list))  # Debug print     
    for key in keys_list:
        print(f"Bid key: {key}")  # Debug print
        
        result_bid = GuileService.GetKV(Class="Bids", key=str(key))
        print(f"Bid data for key {key}:", result_bid,end="\n")  # Debug print
    return jsonify(result), 200 if "error" not in result else 400

# get /bids/user_id/auctions_id per venditore - forse togliere (da veder epoi)

@api_bids.route("/bids/user/<int:user_id>", methods=["GET"])
# ritorna tutte le offerte fatte da un utente, con i relativi dati (asta, asset, ecc) -
#  da vedere se farla fare ad admin o a utente stesso (con controllo che user_id corrisponda a quello del token)
def list_bids_by_user(user_id):
    result = GuileService.GetKeys(
        Class="Bids",
    )
    print("Result from GetKeys (user-search):", result)  # Debug print
    answer = result.get("answer", {})
    keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
    print("Extracted keys list:", keys_list)  # Debug print
    print("-"*100)
    print("# keys:", len(keys_list))  # Debug print 
    user_list = []   
    for key in keys_list:
        print(f"Bid key: {key}")  # Debug print
        
        result_bid = GuileService.GetKV(Class="Bids", key=str(key))
        if result_bid.get("answer", {}).get("value", {}).get("bidderId", "") == user_id:
            user_list.append(result_bid)
        print(f"Bid data for key {key}:", result_bid,end="\n")  # Debug print
    print(len(user_list))
    return jsonify(user_list), 200 if "error" not in result else 400

@api_bids.route("/bids/<string:bid_id>", methods=["GET"])
# route che ritorna i dati di un'offerta specifica, dato il suo ID (key)
def get_bid_by_id(bid_id):
    result = GuileService.GetKV(Class="Bids", key=bid_id)
    print(f"Bid data for key {bid_id}:", result)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400