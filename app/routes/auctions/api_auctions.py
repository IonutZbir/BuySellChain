import os
from datetime import datetime
import glob

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user

from app.models.models import AuctionStatus
from app.services.asset_services import AssetService
from app.services.bid_services import BidService
from app.services.auction_services import AuctionService
from app.services.email_service import EmailService
from app.services.jsend import jsend_response

api_auctions = Blueprint("api_auctions", __name__)


# TODO: Usare jsend_response in tutte le risposte, anche quelle di errore, per mantenere coerenza nell'API

# se startTime e endTime sono nel futuro, l'asta è in stato scheduled, 
# se startTime è passato ma endTime è nel futuro, l'asta è active, 
# se endTime è passato, l'asta è closed
@api_auctions.route("/auctions", methods=["POST"])
@jwt_required()
def create_auction():
    data = request.json
    user = get_current_user()
    sellerId = user.get("id")
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
            return (
                jsonify({"error": "Starting price and minimum increment must be positive numbers"}),
                400,
            )

        # facciamo che min_incr sia almeno il 10% del prezzo di partenza, per evitare aste con incrementi troppo bassi
        if minIncr < 0.1 * startingPrice:
            return (
                jsonify({"error": "Minimum increment must be at least 10% of the starting price"}),
                400,
            )
        if endTime < startTime:
            return jsonify({"error": "End time must be after start time"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid data types for auction fields"}), 400

    result = AuctionService.create_auction(
        assetId, sellerId, startTime, endTime, startingPrice, minIncr
    )
    
    return jsend_response("success", code=200) if result else jsend_response("fail", code=400)


@api_auctions.route("/auctions", methods=["GET"])
def list_auctions():
    # Per le aste attive, recupera e includi nel payload di risposta i dettagli aggiuntivi:
    # - nome e descrizione dell'asset messo all'asta
    # - informazioni del venditore (proprietario dell'asta)
    # Questi dati sono necessari al frontend per visualizzare correttamente i dettagli dell'asta

    auctions = AuctionService.list_all_auctions()

    if not auctions.get("success"):
        return jsend_response("fail", data={"error": auctions.get("error")}, code=404)

    response_data = []

    for auction in auctions.get("auctions", []):
        auction = auction.get("value", [])
        auction_data = {
            "auction_id": auction.get("id"),
            "asset_id": auction.get("asset_id"),
            "seller_id": auction.get("seller_id"),
            "start_time": auction.get("start_time"),
            "end_time": auction.get("end_time"),
            "starting_price": auction.get("starting_price"),
            "min_incr": auction.get("min_incr"),
            "status": auction.get("status"),
            "high_bid_amount": auction.get("high_bid_amount"),
            "high_bid_id": auction.get("high_bid_id"),
            "bid_count": auction.get("bid_count"),
        }
        
        if auction_data["status"] == AuctionStatus.ACTIVE.value or auction_data["status"] == AuctionStatus.SCHEDULED.value or auction_data["status"] == AuctionStatus.LOCKED.value or auction_data["status"] == AuctionStatus.CLOSED.value:
            current_app.logger.debug(f"Processing auction {auction.get('id')} with status {auction_data['status']}")
            # Ottieni i dettagli dell'asset
            asset = AssetService.get_asset(auction.get("asset_id"))
            asset_data = asset.get("data", {}).get("value", {})

            current_app.logger.debug(f"Asset data for auction {auction.get('id')}: {asset_data}")
            
            if asset and asset.get("success"):
                auction_data["asset_title"] = asset_data.get("title")
                auction_data["asset_description"] = asset_data.get("description")
            else:
                auction_data["asset_title"] = "Unknown Asset"
                auction_data["asset_description"] = "Asset details not available"

            image_paths = glob.glob(
                os.path.join(
                    AssetService.base_upload_dir_absolute(),
                    asset_data.get("owner_id", ""),
                    asset_data.get("id", ""),
                    "primary-*.*",
                )
            )

            if image_paths:
                filename = os.path.basename(image_paths[0])

                auction_data["image_url"] = os.path.join(
                    AssetService.base_upload_dir_relative(),
                    asset_data.get("owner_id", ""),
                    asset_data.get("id", ""),
                    filename,
                ).replace("\\", "/")
            else:
                auction_data["image_url"] = os.path.join(
                    AssetService.base_upload_dir_relative(), "default.png"
                ).replace("\\", "/")
                # Fallback a un'immagine di default se non ne troviamo una specifica

        current_app.logger.debug(f"Auction data for auction {auction.get('id')}: {auction_data}")

        response_data.append(auction_data)

    if not response_data:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)

    return jsend_response("success", data={"auctions": response_data})


@api_auctions.route("/auctions/status/<string:status>", methods=["GET"])
def list_auctions_by_status(status):
    result = AuctionService.get_auction_by_status(status)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data={"auctions": result.get("auctions")})


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
@jwt_required()
def delete_auction(auction_id):
    user = get_current_user()
    sellerId = user.get("id")
    result = AuctionService.cancel_auction(auction_id)
    if not result:
        return jsend_response(
            "fail", data={"error": "Errore durante l'eliminazione dell'asta"}, code=500
        )
    return jsend_response("success", code=200)


@api_auctions.route("/auctions/bids/<string:auction_id>", methods=["GET"])
def get_bids_for_auction(auction_id):
    result = BidService.get_all_bids_of_auction(auction_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data={"bids": result.get("bids")})

@api_auctions.route("/auctions/close/<string:auction_id>", methods=["POST"])
def close_auction(auction_id):
    # 1. Recupera tutte le offerte per trovare il vincitore
    result_bids = BidService.get_all_bids_of_auction(auction_id)
    bids_list = result_bids.get("bids", []) if result_bids and result_bids.get("success") else []
    current_app.logger.debug(f"Bids for auction {auction_id}: {bids_list}")
    # 2. Chiudi l'asta sulla blockchain
    result = AuctionService.end_auction_get_winner(auction_id, bids_list)
    
    if not result or not result.get("success"):
        return jsend_response("fail", data={"error": "Errore durante la chiusura dell'asta"}, code=500)
    current_app.logger.debug(f"Winner of auction {auction_id}: {result.get('winner_id')}, Winning bid: {result.get('winning_amount')}")
    
    return jsend_response("success", code=200)

@api_auctions.route("/auctions/lock/<string:auction_id>", methods=["POST"])
def lock_auction(auction_id):
    result = AuctionService.set_locked(auction_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    return jsend_response("success", code=200)

@api_auctions.route("/auctions/active/<string:auction_id>", methods=["POST"])
def activate_auction(auction_id):
    result = AuctionService.set_active(auction_id)
    if not result:
        return jsend_response("fail", data={"error": "Errore del server"}, code=500)
    return jsend_response("success", code=200)
