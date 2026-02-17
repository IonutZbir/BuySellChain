from datetime import datetime
from typing import List, Optional, Dict, Any

from flask import current_app
from app.models.models import Bid
from app.services.guile_services import GuileService


class BidService:
    BID_CLASS = "Bids"

    """Service for managing bid operations"""

    def create_bid(auction_id: str, bidder_id: str, amount: float) -> Dict[str, Any]:
        """Create a new bid"""

        bid = Bid(auction_id, bidder_id, amount)
        current_app.logger.info(f"Created bid: {bid}")  # Debug print
        # Salva l'asta sulla blockchain via Guile
        current_app.logger.info(
            f"Saving bid to blockchain with ID: {bid.get_id()}"
        )  # Debug print
        current_app.logger.info(f"Bid data to save: {bid.to_json()}")  # Debug print
        result = GuileService.AddKV(
            Class=BidService.BID_CLASS, key=bid.get_id(), value=bid.to_json()
        )
        current_app.logger.info(f"Result from Guile AddKV: {result}")  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        return {"success": True}

    def validate_bid(bid_id: str) -> Dict[str, Any]:
        """Validate a bid, setting its status to accepted or rejected"""
        result = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(bid_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        if result.get("answer") is not False and result.get("answer"):
            bid_data = result.get("answer", {}).get("value", {})
            # se amount è pari almeno al minIncremento dell'asta, accettare l'offerta, altrimenti rifiutarla (con motivo "offerta troppo bassa")
            # per fare questo, bisogna prima recuperare i dati dell'asta corrispondente all'offerta, tramite auction_id presente nei dati dell'offerta
            auction_id = bid_data.get("auction_id", "")
            auction_result = GuileService.GetKV(Class="Auctions", key=str(auction_id))
            if "error" in auction_result:
                current_app.logger.error(
                    "Error: {}".format(auction_result.get("error"))
                )
                return {"success": False, "error": auction_result.get("error")}
            if auction_result.get("answer") is not False and auction_result.get(
                "answer"
            ):

                auction_data = auction_result.get("answer", {}).get("value", {})
                status = auction_data.get("status", "")
                print(status)
                if status == "closed" or status == "locked":
                    bid_data["status"] = "rejected"
                    bid_data["reason"] = "Asta chiusa"
                    update_result = GuileService.AddKV(
                        Class=BidService.BID_CLASS, key=str(bid_id), value=bid_data
                    )
                    if "error" in update_result:
                        current_app.logger.error(
                            "Error: {}".format(update_result.get("error"))
                        )
                        return {"success": False, "error": update_result.get("error")}
                    return {"success": True}
                if status == "cancelled":
                    bid_data["status"] = "rejected"
                    bid_data["reason"] = "Asta cancellata"
                    update_result = GuileService.AddKV(
                        Class=BidService.BID_CLASS, key=str(bid_id), value=bid_data
                    )
                    if "error" in update_result:
                        current_app.logger.error(
                            "Error: {}".format(update_result.get("error"))
                        )
                        return {"success": False, "error": update_result.get("error")}
                    return {"success": True}
                min_incr = auction_data.get("min_incr", 0)
                high_bid_amount = auction_data.get("high_bid_amount")
                if high_bid_amount is None:
                    high_bid_amount = auction_data.get("starting_price", 0)
                print(
                    f"Validating bid: bid_amount={bid_data.get('bid_amount', 0)}, high_bid_amount={high_bid_amount}, min_incr={min_incr}"
                )  # Debug print
                if bid_data.get("bid_amount", 0) >= high_bid_amount + min_incr:
                    status = "accepted"
                    reason = None
                else:
                    status = "rejected"
                    reason = "Offerta troppo bassa"
                bid_data["status"] = status
                if reason:
                    bid_data["reason"] = reason
                else:
                    bid_data["reason"] = None
            update_result = GuileService.AddKV(
                Class=BidService.BID_CLASS, key=str(bid_id), value=bid_data
            )
            if "error" in update_result:
                current_app.logger.error("Error: {}".format(update_result.get("error")))
                return {"success": False, "error": update_result.get("error")}
            return {"success": True}

        return {"success": False, "error": "Bid not found"}

    def list_all_bids() -> Dict[str, Any]:
        """List all bids"""
        result = GuileService.GetKeys(Class=BidService.BID_CLASS)
        print("Result from GetKeys:", result)  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        print("Extracted keys list:", keys_list)  # Debug print
        bids = []
        for key in keys_list:
            print(f"Bid key: {key}")  # Debug print

            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data:
                print(f"Bid data for key {key}:", bid_data)  # Debug print
                bids.append({"id": key, "bid_data": bid_data})
        if len(bids) > 0:
            print(f"Bids list: {bids}")  # Debug print
            return {"success": True, "bids": bids}
        return {"success": False, "error": "No bids found"}

    def list_bids_by_user(user_id: str) -> Dict[str, Any]:
        """List all bids by user"""
        result = GuileService.GetKeys(Class=BidService.BID_CLASS)
        print("Result from GetKeys:", result)  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        print("Extracted keys list:", keys_list)  # Debug print
        user_bids = []
        for key in keys_list:
            print(f"Bid key: {key}")  # Debug print

            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data and bid_data.get("value", {}).get("bidderId", "") == user_id:
                print(f"Bid data for key {key}:", bid_data)  # Debug print
                user_bids.append({"id": key, "bid_data": bid_data})
        if len(user_bids) > 0:
            print(f"User bids list: {user_bids}")  # Debug print
            return {"success": True, "bids": user_bids}
        return {"success": False, "error": "No bids found for user"}

    def get_bid_by_id(bid_id: str) -> Dict[str, Any]:
        """Get bid details by ID"""
        result = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(bid_id))
        print(f"Bid data for key {bid_id}:", result)  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        if result.get("answer") is not False and result.get("answer"):
            bid_data = result.get("answer", {}).get("value", {})
            return {"success": True, "id": bid_id, "bid_data": bid_data}

        return {"success": False, "error": "Bid not found"}
