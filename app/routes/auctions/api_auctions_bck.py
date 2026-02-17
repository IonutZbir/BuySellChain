from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from uuid import uuid4
from datetime import datetime
from app.services.guile_services import GuileService
from hashlib import sha256
api_auctions = Blueprint("api_auctions", __name__)


###
# offerte per utente
#imponiamo tempo limite per asta (diviso in finestre temporale)
#poi si aggiurango i dati tipo higBidAmout, higBdId, etc.., minIncrement
#durante l'agiroanemnto status dicenta LOCKED,
#allo scoccare di goni finestra temporale, l'utente può fare al più UNA sola offerta
# y=kx, con y=asta e x=tempo, con k coefficiente da definire (esempio 0.1, 0.2, etc) - da vedere se è meglio fare così o imporre un incremento minimo fisso (esempio 10 euro)
###



@api_auctions.route("/auctions/status/<string:status>", methods=["GET"])
def list_auctions_by_status(status):
    result = GuileService.GetKeys(Class="Auctions")
    print("Result from GetKeys:", result)  # Debug print

    answer = result.get("answer", {})
    keys_list = [
        key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
    ]
    print("Extracted keys list:", keys_list)  # Debug print
    status_list = []
    for key in keys_list:
        print(f"Auction key: {key}")  # Debug print

        result_auction = GuileService.GetKV(Class="Auctions", key=str(key))

        if (
            result_auction.get("answer", {})
            .get("value", {})
            .get("status", "")
            .lower()
            .strip()
            == status
        ):
            status_list.append(result_auction)

        print(f"Auction data for key {key}:", result_auction)  # Debug print
    return jsonify({"auctions": status_list}), 200 if "error" not in result else 400

#aggiunge get /auctions/{id}

@api_auctions.route("/auctions/<string:auction_id>", methods=["GET"])
def get_auction_by_id(auction_id):
    result = GuileService.GetKV(Class="Auctions", key=auction_id)
    return jsonify(result), 200 if "error" not in result else 400


@api_auctions.route("/auctions", methods=["GET"])
def list_auctions():
    result = GuileService.GetKeys(Class="Auctions")
    print("Result from GetKeys:", result)  # Debug print

    answer = result.get("answer", {})
    keys_list = [
        key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
    ]
    print("Extracted keys list:", keys_list)  # Debug print
    
    for key in keys_list:
        print(f"Auction key: {key}")  # Debug print

        result_auction = GuileService.GetKV(Class="Auctions", key=str(key))

        print(f"Auction data for key {key}:", result_auction)  # Debug print
        #to_return_auctions.append(result_auction)
    return jsonify(result), 200 if "error" not in result else 400

@api_auctions.route("/auctions", methods=["POST"])
@jwt_required()
def create_auction():
    ## valdiare dati in  con function apposita, esempio validare che endTime sia dopo startTime, che startingPrice e minIncr siano positivi, etc..
    data = request.json
    data_from_jwt = get_current_user()
    print(f"Data from JWT: {data_from_jwt}")  # Debug print
    print(type(data_from_jwt))  # Debug print
    sellerId = data_from_jwt.get("id")
    #sellerId = 1 # da rimuovere, serve solo per testare senza autenticazione
    highBidId = None
    highBidAmount = None
    bidCount = 0
    status = "active"
    #assetId = data.get("assetId")
    assetId = data.get("assetId") # da rimuovere, serve solo per testare senza autenticazione
    value = {
        "assetId": assetId,
        "sellerId": sellerId,
        "startTime": data.get("startTime"),
        "endTime": data.get("endTime"),
        "startingPrice": data.get("startingPrice"),
        "minIncr": data.get("minIncr"),
        "highBidId": highBidId,
        "highBidAmount": highBidAmount,
        "bidCount": bidCount,
        "status": status,
    }
    key = sha256(str(value).encode() + str(uuid4()).encode()).hexdigest()  # Genera un hash unico per l'asta
    print(f"Creata Asta da Frontend: {key}")
    ### Metadati da Frontend:
    # {assetId, sellerI d,startTime, endTime, startingPrice, minIncr, 
    #highBidId inizio Null, poi ricalcolato - stessa cosa higBidAmount (sarebbe offerta vincetnte)
    #bidCount inizio NUll, poi aggiunrato alla fine di ogni asta, quando si sa a quale asta è associato l'asset
    #status inizio "active", poi "closed" alla fine dell'asta, quando si sa a quale asta è associato l'asset
    #key = hash value + Nonce (true random generator)/UUID (mo vediamo)
    ###
    
    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Auctions", key=key, value=value
    )
    # func che modifica asset su blockchain, aggiungendo currentAuctionId = key dell'asta appena creata, e status = "locked"
    return jsonify(result), 200 if "error" not in result else 400


#fare funzione che prende immagini da cartelle su webserver, con nome corrispondente all'id dell'asta, e le aggiunge agli oggetti delle aste


#@api_auctions.route("/auctions/update", methods=["PUT"])