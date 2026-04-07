from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_current_user

from app.services.bid_services import BidService
from app.services.jsend import jsend_response

api_bids = Blueprint("api_bids", __name__)


@api_bids.route("/bids", methods=["POST"])
@jwt_required()
def create_bid():
    data = request.json
    bidder_id = get_current_user()["id"]
    auction_id = data.get("auction_id")
    amount = data.get("amount")

    if not all([auction_id, amount]):
        return jsend_response("fail", data={"error": "Missing required fields"}, code=400)
    try:
        amount = float(amount)
        if amount <= 0:
            return jsend_response(
                "fail", data={"amount": "Amount must be a positive number"}, code=400
            )
    except (ValueError, TypeError):
        return jsend_response("fail", data={"amount": "Amount must be numeric"}, code=400)

    result = BidService.create_bid(auction_id, bidder_id, amount)

    if not result.get("success"):
        return jsend_response("error", message="Errore del server", code=500)
    else:
        if not result.get("validate_success"):
            return jsend_response("fail", data={"error": result.get("Bid_status_reason")}, code=400)

    return jsend_response("success", code=200)


@api_bids.route("/bids", methods=["GET"])
@jwt_required()
def list_bids():
    result = BidService.list_all_bids()
    if not result:
        return jsend_response("error", message="Errore del server", code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data=result.get("bids"))


@api_bids.route("/bids/user/", methods=["GET"])
@jwt_required()
def list_bids_by_user():
    user_id = get_current_user()["id"]
    result = BidService.list_bids_by_user(user_id)
    if not result:
        return jsend_response("error", message="Errore del server", code=500)
    if not result.get("success"):
        return jsend_response("fail", data={"error": result.get("error")}, code=404)
    return jsend_response("success", data=result.get("bids"))


@api_bids.route("/bids/latest/<auction_id>", methods=["GET"])
@jwt_required()
def get_latest_bid_for_auction(auction_id):
    bidderId = get_current_user()["id"]
    result = BidService.get_latest_bid_for_auction(auction_id, bidderId)

    if not result.get("success"):
        return jsend_response("error", message=result.get("error", "Errore del server"), code=500)

    return jsend_response("success", data={"latest_bid": result.get("latest_bid")})

@api_bids.route("/bids/total/<auction_id>", methods=["GET"])
@jwt_required()
def get_total_bids_for_auction(auction_id):
    result = BidService.get_total_bids_for_auction(auction_id)

    if not result.get("success"):
        return jsend_response("error", message=result.get("error", "Errore del server"), code=500)

    return jsend_response("success", data={"total_bids": result.get("total_bids"),"total_rejected_bids": result.get("total_rejected_bids"), "total_valid_bids": result.get("total_valid_bids")})

@api_bids.route("/bids/allowed_timeframe", methods=["GET"])
def get_allowed_bid_timeframe():
    result = BidService.get_allowed_bid_timeframe()

    if not result.get("success"):
        return jsend_response("error", message=result.get("error", "Errore del server"), code=500)

    return jsend_response(
        "success",
        data={
            "allowed_time_start": result.get("allowed_time_start"),
            "allowed_time_end": result.get("allowed_time_end"),
        },
    )