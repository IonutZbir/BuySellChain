import datetime
from typing import List, Dict, Any

from flask import current_app

from app.models.models import Bid, AuctionStatus, BidStatus
from app.services.guile_services import GuileService
from app.services.auction_services import AuctionService
import json

class BidService:
    BID_CLASS = "Bids"
    BID_ALLOWED_TIME_START = datetime.time(9, 0)
    BID_ALLOWED_TIME_END = datetime.time(14, 54)

    """Service for managing bid operations"""

    def create_bid(auction_id: str, bidder_id: str, amount: float) -> Dict[str, Any]:
        """_summary_

        Args:
            auction_id (str): _id dell'asta a cui si vuole fare l'offerta
            bidder_id (str): _id dell'utente che fa l'offerta
            amount (float): importo dell'offerta

        Returns:
            Dict[str, Any]: {"success": bool, "validate_success": bool, "Bid_status": str, "Bid_status_reason": str} - success indica se l'operazione di creazione è andata a buon fine, validate_success indica se l'offerta è stata approvata o rifiutata, Bid_status indica lo stato dell'offerta (approved/rejected), Bid_status_reason indica il motivo del rifiuto in caso di offerta rifiutata
        """        

        current_app.logger.info(f"Creating bid for auction_id: {auction_id}, bidder_id: {bidder_id}, amount: {amount}")
        
        validate_result = BidService._validate_bid(auction_id, bidder_id, amount)
        
        current_app.logger.info(f"Validation result: {validate_result}")

        bid = Bid(auction_id, bidder_id, amount,status=validate_result.get("bid_status"), reason=validate_result.get("bid_status_reason"))

        result = GuileService.AddKV(
            Class=BidService.BID_CLASS, key=bid.get_id(), value=bid.to_json()
        )
        
        
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}
        
        current_app.logger.info(f"Bid created with ID: {bid.get_id()}") 
        
        return {"success": True, "validate_success": validate_result.get("success"), "Bid_status": validate_result.get("bid_status"), "Bid_status_reason": validate_result.get("error") if not validate_result.get("success") else None} 

    def _validate_bid(auction_id: str, bidder_id: str, amount: float) -> Dict[str, Any]:
        """Validate a bid for an auction.
        Performs validation checks on a bid submission to ensure:
        - Auction exists and is active (rejects closed or cancelled auctions)
        - Bidder is not the auction seller
        - Bid amount meets minimum increment requirement
        - Bid amount exceeds the previous highest bid for that auction
        - Current date is within the auction's start and end dates and respects the time range allowed for bids (e.g., bids allowed only from 1 PM to 4 PM)

        Args:
            auction_id (str): _id dell'asta a cui si vuole fare l'offerta
            bidder_id (str): _id dell'utente che fa l'offerta
            amount (float): importo dell'offerta

        Returns:
            Dict[str, Any]: {"success": bool, "bid_status": str, "bid_status_reason": str} - success indica se l'offerta è stata approvata o rifiutata, bid_status indica lo stato dell'offerta (approved/rejected), bid_status_reason indica il motivo del rifiuto in caso di offerta rifiutata
        """    

        bid_status = ""
        bid_status_reason = ""
        current_time = datetime.datetime.now().time()

        auction_result = AuctionService.get_auction(auction_id)
        if not auction_result.get("success"):
            current_app.logger.error("Error: {}".format(auction_result.get("error")))
            return {"success": False, "error": auction_result.get("error")}

        if auction_result.get("auction_data"):
            auction_data = auction_result.get("auction_data", {})
            if auction_data.get("status") != AuctionStatus.ACTIVE.value:
                bid_status = BidStatus.REJECTED.value
                bid_status_reason = "Auction is not active"
                return {"success": False, "error": "Auction is not active", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            if auction_data.get("seller_id") == bidder_id:
                bid_status = BidStatus.REJECTED.value
                bid_status_reason = "Bidder cannot be the seller"
                return {"success": False, "error": "Bidder cannot be the seller", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            
            if not (BidService.BID_ALLOWED_TIME_START <= current_time <= BidService.BID_ALLOWED_TIME_END):
                bid_status = BidStatus.REJECTED.value
                bid_status_reason = "Bid is not within the allowed time frame"
                return {"success": False, "error": "Bid is not within the allowed time frame", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            
            min_incr = auction_data.get("min_incr", 0)
            
            get_all_bids_result = BidService.list_bids_by_user(bidder_id)
            
            all_bids = get_all_bids_result.get("bids", [])
            
            last_bid_amount = auction_data.get("starting_price", 0)
            for bid in all_bids:
                bid_data = bid.get("bid_data", {}).get("value", {})
                if bid_data.get("auction_id") == auction_id:
                    if bid_data.get("bid_amount", 0) > last_bid_amount:
                        last_bid_amount = bid_data.get("bid_amount", 0)
            
            current_app.logger.debug(f"Last bid amount for auction {auction_id}: {last_bid_amount}")  # Debug print
            if amount < last_bid_amount+min_incr:
                bid_status = BidStatus.REJECTED.value
                bid_status_reason = f"Bid amount must be greater than current highest bid ({last_bid_amount}) plus minimum increment ({min_incr})"
                
                return {"success": False, "error": f"Offerta rifiutata, deve essere almeno pari a ({last_bid_amount}) più ({min_incr})", "bid_status": bid_status, "bid_status_reason": bid_status_reason}
            
        current_app.logger.info("Bid validated successfully")
        return {"success": True, "bid_status": BidStatus.ACCEPTED.value}

    def get_allowed_bid_timeframe() -> Dict[str, Any]:
        """Get the allowed time frame for placing bids.

        Returns:
            Dict[str, Any]: {"success": bool, "allowed_time_start": str, "allowed_time_end": str} - success indicates if the operation was successful, allowed_time_start is the start time for placing bids (in HH:MM format), allowed_time_end is the end time for placing bids (in HH:MM format)
        """
        allowed_time_start = BidService.BID_ALLOWED_TIME_START.strftime("%H:%M")
        allowed_time_end = BidService.BID_ALLOWED_TIME_END.strftime("%H:%M")
        return {"success": True, "allowed_time_start": allowed_time_start, "allowed_time_end": allowed_time_end}

    def list_all_bids() -> Dict[str, Any]:
        """List all bids"""
        
        current_app.logger.info("Listing all bids")
        
        result = GuileService.GetKeys(Class=BidService.BID_CLASS)
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        bids = []
        for key in keys_list:
            current_app.logger.debug(f"Processing bid key: {key}")
            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data:
                bids.append({"id": key, "bid_data": bid_data})
        if len(bids) > 0:
            current_app.logger.info(f"Total bids found: {len(bids)}")
            return {"success": True, "bids": bids}
        
        current_app.logger.warning("No bids found")
        return {"success": False, "error": "No bids found"}

    def list_bids_by_user(user_id: str) -> Dict[str, Any]:
        """list all bids by user

        Args:
            user_id (str): _id dell'utente di cui si vogliono elencare le offerte

        Returns:
            Dict[str, Any]: {"success": bool, "bids": List[Dict[str, Any]], "error": str} - success indica se l'operazione è andata a buon fine, bids è la lista delle offerte dell'utente (se success è True), error è il messaggio di errore (se success è False)
        """
        
        current_app.logger.info(f"Listing bids for user_id: {user_id}")
        
        result = GuileService.GetKeys(Class=BidService.BID_CLASS)
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        answer = result.get("answer", {})
        keys_list = [
            key[0] if isinstance(key, list) else key for key in answer.get("keys", [])
        ]
        
        current_app.logger.debug(f"Total bid keys found: {len(keys_list)}")
        
        user_bids = []
        for key in keys_list:
            current_app.logger.debug(f"Processing bid key: {key}")
            result_bid = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(key))
            bid_data = result_bid.get("answer", {})
            if bid_data and bid_data.get("value", {}).get("bidder_id", "") == user_id:
                user_bids.append({"id": key, "bid_data": bid_data})
        if len(user_bids) > 0:
            current_app.logger.info(f"Total bids found for user {user_id}: {len(user_bids)}")
            return {"success": True, "bids": user_bids}
        
        current_app.logger.warning(f"No bids found for user {user_id}")
        return {"success": False, "error": "No bids found for user"}

    def get_bid_by_id(bid_id: str) -> Dict[str, Any]:
        """Get a bid by its ID

        Args:
            bid_id (str): _id dell'offerta da recuperare

        Returns:
            Dict[str, Any]: {"success": bool, "id": str, "bid_data": Dict[str, Any], "error": str} - success indica se l'operazione è andata a buon fine, id è l'id dell'offerta (se success è True), bid_data è il dizionario con i dati dell'offerta (se success è True), error è il messaggio di errore (se success è False)
        """
             
        current_app.logger.info(f"Getting bid by ID: {bid_id}")
        
        result = GuileService.GetKV(Class=BidService.BID_CLASS, key=str(bid_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        if result.get("answer") is not False and result.get("answer"):
            bid_data = result.get("answer", {}).get("value", {})
            current_app.logger.info(f"Bid found for ID: {bid_id}")
            return {"success": True, "id": bid_id, "bid_data": bid_data}

        current_app.logger.warning(f"Bid not found for ID: {bid_id}")
        return {"success": False, "error": "Bid not found"}

    def get_all_bids_of_auction(auction_id: str) -> List[Dict[str, Any]]:
        """Get all bids for an auction

        Args:
            auction_id (str): _id dell'asta di cui si vogliono recuperare le offerte

        Returns:
            List[Dict[str, Any]]: {"success": bool, "bids": List[Dict[str, Any]], "error": str} - success indica se l'operazione è andata a buon fine, bids è la lista delle offerte per l'asta (se success è True), error è il messaggio di errore (se success è False)
        """                
        
        current_app.logger.debug(f"Getting all bids for auction_id: {auction_id}")   
        all_bids = BidService.list_all_bids()
        if not all_bids.get("success"):
            return []
        bids = []
        for bid in all_bids.get("bids", []):
            bid_data = bid.get("bid_data", {}).get("value", {})
            if bid_data.get("auction_id") == auction_id:
                bids.append(bid_data)
        
        # ordina bid in base a timestamp
        bids.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        if len(bids) > 0:
            current_app.logger.info(f"Total bids found for auction {auction_id}: {len(bids)}")
            return {"success": True, "bids": bids}
        
        current_app.logger.warning(f"No bids found for auction {auction_id}")
        return {"success": False, "error": "No bids found for auction"}
    
    def get_latest_bid_for_auction(auction_id: str, bidderId:str) -> Dict[str, Any]:
        """get latest bid for an auction

        Args:
            auction_id (str): _id dell'asta di cui si vuole recuperare l'offerta più alta
            bidderId (str): _id dell'utente che fa la richiesta, usato per escludere le offerte dello stesso utente (se l'utente ha fatto più offerte, viene restituita l'offerta più alta tra quelle fatte dall'utente)

        Returns:
            Dict[str, Any]: {"success": bool, "latest_bid": float, "error": str} - success indica se l'operazione è andata a buon fine, latest_bid è l'importo dell'offerta più alta per l'asta (se success è True), error è il messaggio di errore (se success è False)
        """        
        
        latest_bid = 0
        
        current_app.logger.debug(f"Getting latest bid for auction_id: {auction_id} and bidderId: {bidderId}")
        
        # prendo i dati dell'asta
        auction_data = AuctionService.get_auction(auction_id)
        
        if auction_data.get("auction_data").get("seller_id") == bidderId:
            current_app.logger.warning(f"Seller {bidderId} cannot be the bidder for auction {auction_id}")
            return {"success": False, "error": "Seller cannot be the bidder"}
        all_bids = BidService.list_bids_by_user(bidderId)

        if not all_bids.get("success"):
             return {"success": True, "latest_bid": latest_bid}
        
        for bid in all_bids.get("bids", []):
            bid_data = bid.get("bid_data", {}).get("value", {})
            if bid_data.get("auction_id") == auction_id:
                if not latest_bid or bid_data.get("bid_amount", 0) > latest_bid:
                    latest_bid = bid_data.get("bid_amount")
        
        current_app.logger.info(f"Latest bid for auction {auction_id}: {latest_bid}")        
        
        return {"success": True, "latest_bid": latest_bid}
    
    def get_total_bids_for_auction(auction_id: str) -> Dict[str, Any]:
        """get total number of bids for an auction

        Args:
            auction_id (str): _id dell'asta di cui si vuole recuperare il numero totale di offerte
        """
        
        total_bids = 0
        total_rejected_bids = 0
        total_valid_bids = 0
        current_app.logger.debug(f"Getting total bids for auction_id: {auction_id}")
        
        all_bids = BidService.list_all_bids()
        if not all_bids.get("success"):
            return {"success": False, "error": all_bids.get("error")}
        
        for bid in all_bids.get("bids", []):
            bid_data = bid.get("bid_data", {}).get("value", {})
            if bid_data.get("auction_id") == auction_id:
                total_bids += 1
                if bid_data.get("status") == BidStatus.REJECTED.value:
                    total_rejected_bids += 1
                elif bid_data.get("status") == BidStatus.ACCEPTED.value:
                    total_valid_bids += 1
        current_app.logger.info(f"Total bids for auction {auction_id}: {total_bids}")
        current_app.logger.info(f"Total rejected bids for auction {auction_id}: {total_rejected_bids}")
        current_app.logger.info(f"Total valid bids for auction {auction_id}: {total_valid_bids}")

        return {"success": True, "total_bids": total_bids, "total_rejected_bids": total_rejected_bids, "total_valid_bids": total_valid_bids}
    
    def get_bid_timestamp_txid(bid_id: str):
        """get the timestamp and txid of a bid

        Args:
            bid_id (str): _id dell'offerta di cui si vogliono recuperare timestamp e txid

        Returns:
            Dict[str, Any]: {"success": bool, "timestamp": str, "txid": str, "error": str} - success indica se l'operazione è andata a buon fine, timestamp è la data e ora in cui è stata fatta l'offerta (se success è True), txid è l'id della transazione associata all'offerta (se success è True), error è il messaggio di errore (se success è False)
        """        
        
        current_app.logger.debug(f"Getting timestamp, txid, amount and bidder for bid_id: {bid_id}")
        
        result = GuileService.GetKeyHistory(Class=BidService.BID_CLASS, key=str(bid_id))
        if "error" in result:
            current_app.logger.error("Error: {}".format(result.get("error")))
            return {"success": False, "error": result.get("error")}

        if result.get("answer") is not False and result.get("answer"):
            bid_data = result.get("answer", {})
            dict = bid_data[0]
            timestamp_raw = dict.get("timestamp")
            # aggiungo 2 ore al timestamp per allinearlo all'orario italiano (Guile restituisce il timestamp in UTC)
            # timestamp è stringa, il formato ha questo stile 2026-04-02T14:30:20.504612776Z
            timestamp = None
            if timestamp_raw:
                timestamp_clean = timestamp_raw.rstrip("Z")
                if "." in timestamp_clean:
                    base, frac = timestamp_clean.split(".", 1)
                    frac = (frac + "000000")[:6]  # Python gestisce microsecondi, non nanosecondi
                    timestamp_dt = datetime.datetime.fromisoformat(f"{base}.{frac}")
                else:
                    timestamp_dt = datetime.datetime.fromisoformat(timestamp_clean)
                timestamp = (timestamp_dt + datetime.timedelta(hours=2)).isoformat()
            current_app.logger.debug(f"Raw timestamp: {timestamp_raw}, Cleaned timestamp: {timestamp_clean}, Final timestamp: {timestamp}")
            
            txid = dict.get("txId")
            data = json.loads(dict.get("data", {})).get("value", {})
            bidder = data.get("bidder_id", "")
            bid_amount = data.get("bid_amount", 0)
            reason = data.get("reason", "")
            status = data.get("status", "")
            current_app.logger.info(f"Timestamp for bid {bid_id}: {timestamp}, TxID: {txid}")
            return {"success": True, "timestamp": timestamp, "txid": txid, "bidder": bidder, "bid_amount": bid_amount, "reason": reason, "status": status}

        current_app.logger.warning(f"Bid not found for ID: {bid_id}")
        return {"success": False, "error": "Bid not found"}
