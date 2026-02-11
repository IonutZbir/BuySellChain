from flask import Blueprint, jsonify, request

from app.services.guile_services import GuileService


api_bids = Blueprint("api_bids", __name__)

@api_bids.route("/bids", methods=["POST"])
def create_bid():
    data = request.json

    ### Metadati da Frontend:
    # {auctionId, bidderId, amount, }
    # TIMESTAMPT calcolato qui
    # validare amount >= basePrice+increment (da fare lato frontend, ma poi anche qui per sicurezza)
    # - se mgarriore uguale status accettato, altrimenti stauts rigettato (con Reason)
    #validare anche che l'asta sia ancora attiva (non scaduta, non conclusa, ecc)
    #- se utente cerca di fare Bid per asta non attiva, rigettare con Reason "Auction not active"

    
    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Bids", key=data.get("key"), value=data.get("value")
    )
    print("Result from AddKV:", result)  # Debug print
    return jsonify(result), 200 if "error" not in result else 400

# vedere se farla fare ad admin
@api_bids.route("/bids", methods=["GET"])
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

@api_bids.route("/bids/<string:user_id>", methods=["GET"])
def list_bids_by_user(user_id):
    result = GuileService.GetKeys(
        Class="Bids",
    )
    print("Result from GetKeys:", result)  # Debug print
    answer = result.get("answer", {})
    keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
    print("Extracted keys list:", keys_list)  # Debug print
    print("-"*100)
    print("# keys:", len(keys_list))  # Debug print 
    user_list = []   
    for key in keys_list:
        print(f"Bid key: {key}")  # Debug print
        
        result_bid = GuileService.GetKV(Class="Bids", key=str(key))
        if result_bid.get("answer", {}).get("value", {}).get("bidderId", "").strip() == user_id:
            user_list.append(result_bid)
        print(f"Bid data for key {key}:", result_bid,end="\n")  # Debug print
    print(len(user_list))
    return jsonify(user_list), 200 if "error" not in result else 400