
from datetime import datetime
from typing import Dict, Any

from flask import current_app

from app.models.models import Auction
from app.services.guile_services import GuileService
from app.services.email_service import EmailService

class AuctionService:
    AUCTION_CLASS = "Auctions"

    """Service for managing auction operations"""

    def create_auction(
        asset_id: str,
        seller_id: str,
        start_time: datetime,
        end_time: datetime,
        starting_price: float,
        min_incr: float,
    ) -> Dict[str, Any]:
        """

        Args:
            asset_id (str): id dell'asset messo all'asta
            seller_id (str): id del venditore (utente che crea l'asta)
            start_time (datetime): inzio dell'asta
            end_time (datetime): fine dell'asta
            starting_price (float): prezzo iniziale dell'asta
            min_incr (float): incremento minimo per ogni offerta

        Returns:
            Dict[str, Any]: {"success": True} se l'asta è stata creata con successo, {"success": False, "error": "error message"} altrimenti
        """

        # aggiungere controllo su start e endTime prima di creare il modello
        if start_time > datetime.now():
            status = "scheduled"
        else:
            status = "active"

        auction = Auction(asset_id, seller_id, start_time, end_time, starting_price, min_incr, status)

        result = GuileService.AddKV(
            Class=AuctionService.AUCTION_CLASS, key=auction.get_id(), value=auction.to_json()
        )

        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return False

        current_app.logger.info(f"Auction created with ID: {auction.get_id()}")

        return True

    def get_auction(auction_id: str) -> Dict[str, Any]:
        """
        Args:
            auction_id (str): id dell'asta da recuperare

        Returns:
            Dict[str, Any]: {"success": True, "id": auction_id, "auction_data": auction_data} se l'asta è stata recuperata con successo, {"success": False, "error": "error message"} altrimenti
        """

        current_app.logger.info(f"Retrieving auction with ID: {auction_id}")

        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            return {"success": True, "id": auction_id, "auction_data": auction_data}

        current_app.logger.warning(f"Auction with ID {auction_id} not found")
        return {"success": False, "error": "Auction not found"}

    def list_all_auctions() -> Dict[str, Any]:
        """

        Returns:
            Dict[str, Any]: {"success": True, "auctions": [{"id": auction_id, "value": auction_data}, ...]} se le aste sono state recuperate con successo, {"success": False, "error": "error message"} altrimenti
        """

        current_app.logger.info("Listing all auctions")

        result = GuileService.GetKeys(Class=AuctionService.AUCTION_CLASS)
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        answer = result.get("answer", {})
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]

        auctions = []
        for key in keys_list:
            current_app.logger.info(f"Retrieving auction with key: {key}")

            result_auction = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(key))
            auction_data = result_auction.get("answer", {}).get("value", {})
            if auction_data:
                auctions.append({"id": key, "value": auction_data})
        if len(auctions) > 0:
            current_app.logger.info(f"Found {len(auctions)} auctions")
            return {"success": True, "auctions": auctions}

        current_app.logger.warning("No auctions found in blockchain")
        return {"success": False, "error": "No auctions found"}

    def end_auction_get_winner(auction_id: str, bids_list: list) -> Dict[str, Any]:
        current_app.logger.info(f"Ending auction with ID: {auction_id} and determining winner")
        
        result = AuctionService.get_auction(auction_id)
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}
        
        current_app.logger.debug(f"Result from get_auction: {result}")
        winner_id = None
        auction_data = result.get("auction_data")
        if auction_data is not False and auction_data:
            auction_data["status"] = "closed" # Impostiamo su closed
            print("Auction data before determining winner:", auction_data)  # Debug print
            # Calcolo del vincitore
            for bid in bids_list:
                current_app.logger.debug(f"Evaluating bid: {bid} for auction {auction_id}")
                if bid.get("auction_id") == auction_id:
                    if auction_data.get("high_bid_amount") is None:
                        auction_data["high_bid_amount"] = 0
                    if bid.get("bid_amount", 0) > auction_data.get("high_bid_amount"):
                        auction_data["high_bid_amount"] = bid.get("bid_amount", 0)
                        auction_data["high_bid_id"] = bid.get("id")
                        winner_id = bid.get("bidder_id")

            # SALVATAGGIO IN BLOCKCHAIN (Mancava nel tuo codice originario!)
            result_update = GuileService.AddKV(
                Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data
            )
            
            if "error" in result_update:
                current_app.logger.error("Error updating blockchain: {}".format(result_update.get("error")))
                return {"success": False, "error": result_update.get("error")}
                
            current_app.logger.info(f"Auction {auction_id} closed. Winner Bid: {auction_data.get('high_bid_id')}")
            
            send_email_result = EmailService.send_email_to_winner(winner_id, auction_id, auction_data)
            if not send_email_result.get("success"):
                current_app.logger.error(f"Error sending email to winner: {send_email_result.get('error')}")
                # Non ritorniamo un errore critico se l'email fallisce, ma logghiamo l'errore

            return {"success": True, "winner_id": auction_data.get("high_bid_id"), "winning_amount": auction_data.get("high_bid_amount")}

        return {"success": False, "error": "Auction not found"}

    def set_locked(auction_id: str) -> bool:
        """_summary_

        Args:
            auction_id (str): id dell'asta da mettere in stato locked

        Returns:
            bool: True se l'asta è stata aggiornata con successo, False altrimenti
        """        
        
        current_app.logger.info(f"Setting auction with ID: {auction_id} to locked")
        
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "locked"
            result_update = GuileService.AddKV(
                Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data
            )
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get("error")))
                return False
            
            current_app.logger.info(f"Auction with ID {auction_id} set to locked")
            
            return True
        return False
    
    def set_active(auction_id: str) -> bool:
        """_summary_

        Args:
            auction_id (str): id dell'asta da mettere in stato active

        Returns:
            bool: True se l'asta è stata aggiornata con successo, False altrimenti
        """        
        
        current_app.logger.info(f"Setting auction with ID: {auction_id} to active")
        
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "active"
            result_update = GuileService.AddKV(
                Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data
            )
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get("error")))
                return False
            
            current_app.logger.info(f"Auction with ID {auction_id} set to active")
            
            return True
        return False

    def get_auction_by_status(status: str) -> str:
        """Get auctions by status"""
        result = GuileService.GetKeys(Class=AuctionService.AUCTION_CLASS)
        print("Result from GetKeys:", result)  # Debug print

        answer = result.get("answer", {})
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
        print("Extracted keys list:", keys_list)  # Debug print
        status_list = []
        for key in keys_list:
            print(f"Auction key: {key}")  # Debug print

            result_auction = (
                GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(key))
                .get("answer", {})
                .get("value", {})
            )

            if result_auction.get("status", "").lower().strip() == status:
                status_list.append(result_auction)

            print(f"Auction data for key {key}:", result_auction)  # Debug print
        if len(status_list) > 0:
            print(f"Auctions with status {status}: {status_list}")  # Debug print
            return {"success": True, "auctions": status_list}
        return {"success": False, "error": f"No auctions found with status {status}"}

