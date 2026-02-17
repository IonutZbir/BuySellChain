from datetime import datetime
from typing import List, Optional, Dict, Any

from flask import current_app

from app.models.models import Auction
from app.services.guile_services import GuileService

class AuctionService:
    AUCTION_CLASS = "Auctions"

    """Service for managing auction operations"""
    
    def create_auction(asset_id: str, seller_id: str, start_time: datetime, end_time: datetime, starting_price: float, min_incr: float) -> Dict[str, Any]:
        """Create a new auction"""
        
        auction = Auction(asset_id, seller_id, start_time, end_time, starting_price, min_incr)
        current_app.logger.info(f"Created auction: {auction}")  # Debug print
        # Salva l'asta sulla blockchain via Guile
        current_app.logger.info(f"Saving auction to blockchain with ID: {auction.get_id()}")  # Debug print
        current_app.logger.info(f"Auction data to save: {auction.to_json()}")  # Debug print
        result = GuileService.AddKV(Class=AuctionService.AUCTION_CLASS, key=auction.get_id(), value=auction.to_json())
        current_app.logger.info(f"Result from Guile AddKV: {result}")  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return False

        return True
    
    def get_auction(auction_id: str) -> Dict[str, Any]:
        """Retrieve auction details from id"""
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            return {"success": True, "id": auction_id, "auction_data": auction_data}
        
        return {"success": False, "error": "Auction not found"}
    
    def list_all_auctions() -> Dict[str, Any]:
        """List all auctions"""
        result = GuileService.GetKeys(Class=AuctionService.AUCTION_CLASS)
        print("Result from GetKeys:", result)  # Debug print
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return {"success": False, "error": result.get('error')}
        
        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        print("Extracted keys list:", keys_list)  # Debug print
        auctions = []
        for key in keys_list:
            print(f"Auction key: {key}")  # Debug print

            result_auction = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(key))
            auction_data = result_auction.get("answer", {})
            if auction_data:
                print(f"Auction data for key {key}:", auction_data)  # Debug print
                auctions.append({"id": key, "auction_data": auction_data})
        if len(auctions)>0:
            print(f"Auctions list: {auctions}")  # Debug print
            return {"success": True, "auctions": auctions}
        return {"success": False, "error": "No auctions found"}
    
    def get_bids(self, auction_id: str) -> List[Dict[str, Any]]:
        """Get all bids for an auction"""
        pass
    
    def set_locked(auction_id: str) -> bool:
        """Set auction status to locked"""
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return False
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "locked"
            result_update = GuileService.AddKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data)
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get('error')))
                return False
            return True
        return False
    
    def end_auction(auction_id: str) -> Dict[str, Any]:
        """End an auction and determine winner"""
        # aggiornanre los tato a locekd, calcolare vincitore, aggiornare a closed, e basta
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return {"success": False, "error": result.get('error')}
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "closed"
            for bid in auction_data.get("bids", []):
                if bid.get("amount", 0) > auction_data.get("highBidAmount", 0):
                    auction_data["highBidId"] = bid.get("bidderId")
                    auction_data["highBidAmount"] = bid.get("amount")
            auction_data["bidCount"] = len(auction_data.get("bids", []))
            result_update = GuileService.AddKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data)
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get('error')))
                return {"success": False, "error": result_update.get('error')}
            return {"success": True, "message": f"Auction {auction_id} closed successfully"}
    
    def get_winner(auction_id: str) -> Dict[str, Any]:
        """Get winner of an auction"""
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return {"success": False, "error": result.get('error')}
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            if auction_data.get("status", "") == "closed":
                winner_id = auction_data.get("highBidId")
                winning_amount = auction_data.get("highBidAmount")
                return {"success": True, "winner_id": winner_id, "winning_amount": winning_amount}
            else:
                return {"success": False, "error": "Auction is not closed yet"}
        return {"success": False, "error": "Auction not found"}
    
    def cancel_auction(auction_id: str) -> bool:
        """Cancel an auction"""
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get('error')))
            return False
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "cancelled"
            result_update = GuileService.AddKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data)
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get('error')))
                return False
            return True
        return False
    
    def get_auction_by_status(status: str) -> str:
        """Get auctions by status"""
        result = GuileService.GetKeys(Class=AuctionService.AUCTION_CLASS)
        print("Result from GetKeys:", result)  # Debug print

        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        print("Extracted keys list:", keys_list)  # Debug print
        status_list = []
        for key in keys_list:
            print(f"Auction key: {key}")  # Debug print

            result_auction = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(key))

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
        if len(status_list) > 0:
            print(f"Auctions with status {status}: {status_list}")  # Debug print
            return {"success": True, "auction_by_status": status_list}
        return {"success": False, "error": f"No auctions found with status {status}"}
