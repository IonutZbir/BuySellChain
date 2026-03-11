
from datetime import datetime
from typing import Dict, Any

from flask import current_app

from app.models.models import Auction
from app.services.guile_services import GuileService


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

        auction = Auction(asset_id, seller_id, start_time, end_time, starting_price, min_incr)

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

    def end_auction_get_winner(auction_id: str, bids_list: dict) -> Dict[str, Any]:
        """

        Args:
            auction_id (str): id dell'asta da chiudere
            bids_list (dict): lista di tutte le offerte presenti nella blockchain, da cui estrarre quelle relative all'asta in questione per determinare il vincitore (bidder_id con offerta più alta)

        Returns:
            Dict[str, Any]: {"success": True, "winner_id": winner_id, "winning_amount": winning_amount} se l'asta è stata chiusa con successo e il vincitore è stato determinato, {"success": False, "error": "error message"} altrimenti
        """

        # TODO: aggiornanre lo stato a locked, calcolare vincitore, aggiornare a closed. Da dare in output anche l'id del vincitore e l'importo vincente (highBidAmount). Poi trovare un modo per mostrarlo solo al vincitore (per ora basta che sia visibile a tutti, poi si può pensare a una soluzione più elegante)

        # Per calcolare il vincitore, prendo tutte le offerte relative a quell'asta (guardando solo le bids che hanno auction_id uguale a quello dell'asta in questione), e prendo quella con bid_amount più alto. Il bidder_id di quella offerta sarà il vincitore, e l'importo sarà highBidAmount. Questi dati vanno poi salvati all'interno dell'asta (highBidId e highBidAmount) insieme allo stato closed.

        current_app.logger.info(f"Ending auction with ID: {auction_id} and determining winner")
        result = AuctionService.get_auction(auction_id)
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "closed"
            for bid in bids_list:
                if bid.get("bid_data", {}).get("auction_id") == auction_id:
                    if bid.get("bid_data", {}).get("bid_amount", 0) > auction_data.get(
                        "high_bid_amount", 0
                    ):
                        auction_data["high_bid_amount"] = bid.get("bid_data", {}).get(
                            "bid_amount", 0
                        )
                        auction_data["high_bid_id"] = bid.get("id")

        # current_app.logger.info(f"Auction with ID {auction_id} closed with winner ID: {auction_data.get('high_bid_id')} and winning amount: {auction_data.get('high_bid_amount')}")
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

    def get_winner(auction_id: str) -> Dict[str, Any]:
        """_summary_

        Args:
            auction_id (str): id dell'asta di cui si vuole conoscere il vincitore

        Returns:
            Dict[str, Any]: {"success": True, "winner_id": winner_id, "winning_amount": winning_amount} se il vincitore è stato determinato con successo, {"success": False, "error": "error message"} altrimenti
        """
        
        # TODO: prendere l'asta, verificare che sia closed, e restituire id del vincitore e importo vincente (highBidId e highBidAmount).
    
        result = GuileService.GetKV(Class=AuctionService.AUCTION_CLASS, key=str(auction_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}
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
            current_app.logger.error("Error: {}".format(result.get("error")))
            return False
        if result.get("answer") is not False and result.get("answer"):
            auction_data = result.get("answer", {}).get("value", {})
            auction_data["status"] = "cancelled"
            result_update = GuileService.AddKV(
                Class=AuctionService.AUCTION_CLASS, key=str(auction_id), value=auction_data
            )
            if "error" in result_update:
                current_app.logger.error("Error: {}".format(result_update.get("error")))
                return False
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
