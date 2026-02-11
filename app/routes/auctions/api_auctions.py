from flask import Blueprint, jsonify, request

from app.services.guile_services import GuileService

api_auctions = Blueprint("api_auctions", __name__)


###
# offerte per utente
#imponiamo tempo limite per asta (diviso in finestre temporale)
#poi si aggiurango i dati tipo higBidAmout, higBdId, etc.., minIncrement
#durante l'agiroanemnto status dicenta LOCKED,
#allo scoccare di goni finestra temporale, l'utente può fare al più UNA sola offerta
# y=kx, con y=asta e x=tempo, con k coefficiente da definire (esempio 0.1, 0.2, etc) - da vedere se è meglio fare così o imporre un incremento minimo fisso (esempio 10 euro)
###



@api_auctions.route("/auctions/<string:status>", methods=["GET"])
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
    return jsonify(result), 200 if "error" not in result else 400


@api_auctions.route("/auctions", methods=["POST"])
def create_auction():
    data = request.json

    ### Metadati da Frontend:
    # {assetId, sellerId,startTime, endTime, startingPrice, minIncr, 
    #highBidId inizio Null, poi ricalcolato - stessa cosa higBidAmount (sarebbe offerta vincetnte)
    #bidCount inizio NUll, poi aggiunrato alla fine di ogni asta, quando si sa a quale asta è associato l'asset
    #status inizio "active", poi "closed" alla fine dell'asta, quando si sa a quale asta è associato l'asset
    #key = hash value + Nonce (true random generator)/UUID (mo vediamo)
    ###

    # Chiamata al servizio che parla con il cli
    result = GuileService.AddKV(
        Class="Auctions", key=data.get("key"), value=data.get("value")
    )
    return jsonify(result), 200 if "error" not in result else 400


