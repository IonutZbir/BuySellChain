from datetime import datetime
from typing import List, Optional, Dict, Any

from flask import current_app
from app.models.models import Bid
from app.services.guile_services import GuileService
from app.services.auction_services import AuctionService

class BidService:
    BID_CLASS = "Bids"

    """Service for managing bid operations"""

    def create_bid(auction_id: str, bidder_id: str, amount: float) -> Dict[str, Any]:
        """Create a new bid"""

        validate_result = BidService.validate_bid(auction_id, bidder_id, amount)
        
        print(f"Validation result for bid creation: {validate_result}")  # Debug print

        bid = Bid(auction_id, bidder_id, amount,status=validate_result.get("bid_status"), reason=validate_result.get("bid_status_reason"))

        # current_app.logger.info(f"Created bid: {bid}")  # Debug print
        # # Salva l'asta sulla blockchain via Guile
        # current_app.logger.info(
        #     f"Saving bid to blockchain with ID: {bid.get_id()}"
        # )  # Debug print
        # current_app.logger.info(f"Bid data to save: {bid.to_json()}")  # Debug print
        result = GuileService.AddKV(
            Class=BidService.BID_CLASS, key=bid.get_id(), value=bid.to_json()
        )
        current_app.logger.info(f"Result from Guile AddKV: {result}")  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}
        return {"success": True, "validate_success": validate_result.get("success"), "Bid_status": validate_result.get("bid_status"), "Bid_status_reason": validate_result.get("error") if not validate_result.get("success") else None} 


    # for validate : verificare esistenza asta, asta aperta -> se asta closed o cancelled rifuta offerta, bidderId != sellerId, amount >= minIncr, amount > amount precedente
    def validate_bid(auction_id: str, bidder_id: str, amount: float) -> Dict[str, Any]:
        """Validate a bid before creation"""

        bid_status = ""
        bid_status_reason = ""

        auction_result = AuctionService.get_auction(auction_id)
        if not auction_result.get("success"):
            #current_app.logger.error("Error: {}".format(auction_result.get("error")))
            return {"success": False, "error": auction_result.get("error")}

        if auction_result.get("auction_data"):

            auction_data = auction_result.get("auction_data", {})
            if auction_data.get("status") != "active":
                bid_status = "rejected"
                bid_status_reason = "Auction is not active"
                return {"success": False, "error": "Auction is not active", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            if auction_data.get("seller_id") == bidder_id:
                bid_status = "rejected"
                bid_status_reason = "Bidder cannot be the seller"
                return {"success": False, "error": "Bidder cannot be the seller", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            min_incr = auction_data.get("min_incr", 0)
            
            get_all_bids_result = BidService.list_bids_by_user(bidder_id)
            
            all_bids = get_all_bids_result.get("bids", [])
            
            last_bid_amount = auction_data.get("starting_price", 0)
            for bid in all_bids:
                bid_data = bid.get("bid_data", {}).get("value", {})
                if bid_data.get("auction_id") == auction_id:
                    if bid_data.get("bid_amount", 0) > last_bid_amount:
                        last_bid_amount = bid_data.get("bid_amount", 0)
            
            print(f"Last bid amount for auction {auction_id}: {last_bid_amount}")  # Debug print
            if amount < last_bid_amount+min_incr:
                bid_status = "rejected"
                bid_status_reason = f"Bid amount must be greater than current highest bid ({last_bid_amount}) plus minimum increment ({min_incr})"
                #last_bid_amount = auction_data.get("starting_price")
                return {"success": False, "error": f"Offerta rifiutata, deve essere almeno pari a ({last_bid_amount}) più ({min_incr})", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            

        return {"success": True, "bid_status": "approved"}


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
        #print("Extracted keys list:", keys_list)  # Debug print
        bids = []
        for key in keys_list:
            #print(f"Bid key: {key}")  # Debug print

            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data:
                #print(f"Bid data for key {key}:", bid_data)  # Debug print
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
            #print(f"Bid key: {key}")  # Debug print

            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data and bid_data.get("value", {}).get("bidder_id", "") == user_id:
                print(f"Bid data for key {key}:", bid_data)  # Debug print
                user_bids.append({"id": key, "bid_data": bid_data})
        if len(user_bids) > 0:
            #print(f"User bids list: {user_bids}")  # Debug print
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

    def get_all_bids_of_auction(auction_id: str) -> List[Dict[str, Any]]:
        """Get all bids for an auction"""
        all_bids = BidService.list_all_bids()
        if not all_bids.get("success"):
            return []
        bids = []
        for bid in all_bids.get("bids", []):
            bid_data = bid.get("bid_data", {}).get("value", {})
            if bid_data.get("auction_id") == auction_id:
                bids.append(bid_data)
        # ordina bid in bae a timestamp
        if len(bids) > 0:
            return {"success": True, "bids": bids}
        return {"success": False, "error": "No bids found for auction"}
    
    def get_latest_bid_for_auction(auction_id: str,bidderId:str) -> Dict[str, Any]:
        """Get the latest bid for an auction"""
        latest_bid=0
        auction_data = AuctionService.get_auction(auction_id)
        if auction_data.get("auction_data").get("seller_id") == bidderId:
            return {"success": False, "error": "Seller cannot be the bidder"}
        all_bids = BidService.list_bids_by_user(bidderId)
        print(f"All bids for bidder {bidderId}:", all_bids)  # Debug print
        if not all_bids.get("success"):
             return {"success": True, "latest_bid": latest_bid}
        print(all_bids)
        
        
        for bid in all_bids.get("bids", []):
            bid_data = bid.get("bid_data", {}).get("value", {})
            if bid_data.get("auction_id") == auction_id:
                if not latest_bid or bid_data.get("bid_amount", 0) > latest_bid:
                    latest_bid = bid_data.get("bid_amount")
        
        print(f"Latest bid for auction {auction_id}: {latest_bid}")  # Debug print
        return {"success": True, "latest_bid": latest_bid}
        