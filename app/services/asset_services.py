from datetime import datetime
from hashlib import sha256
from uuid import uuid4
from app.models.models import Asset, AssetStatus, AssetType
from app.services.guile_services import GuileService
from flask import current_app


class AssetService:
    """Servizio per gestire gli asset sulla blockchain"""

    ASSETS_CLASS = "Assets"

    @staticmethod
    def create_asset(owner_id: str, title: str, description: str, asset_type: AssetType, 
                    size: float, price: float, location: str) -> dict:
        """
        Crea un nuovo asset e lo salva sulla blockchain
        
        Args:
            owner_id: ID del proprietario
            title: Titolo dell'asset
            description: Descrizione dell'asset
            asset_type: Tipo di asset (villa, flat, cottage, ecc.)
            size: Dimensione dell'asset
            price: Prezzo dell'asset
            location: Ubicazione dell'asset
            
        Returns:
            True: se l'asset è creato correttamente. False altrimenti.
        """
        
        asset = Asset(owner_id, title, description, asset_type, size, price, location)
        
        # Salva l'asset sulla blockchain via Guile
        result = GuileService.AddKV(Class=AssetService.ASSETS_CLASS, key=asset.get_id(), value=asset.to_json())
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False

        return True
            
    @staticmethod
    def get_asset(asset_id: str) -> dict:
        """
        Recupera un asset dalla blockchain tramite il suo ID
        
        Args:
            asset_id: ID dell'asset
            
        Returns:
            dict: Dati dell'asset oppure errore
        """
        result = GuileService.GetKV(Class=AssetService.ASSETS_CLASS, key=str(asset_id))
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            asset_data = result.get("answer", {})
            return {"success": True, "id": asset_id, "data": asset_data}
        else:
            return {"success": False, "error": "Asset not found"}


    @staticmethod
    def get_assets_by_user(user_id: str) -> dict:
        """
        Recupera tutti gli asset di un utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Lista degli asset dell'utente
        """
            # Recupera tutti gli ID dei asset
        result = GuileService.GetKeys(Class=AssetService.ASSETS_CLASS)
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False
        
        answer = result.get("answer", {})
        
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
        
        user_assets = []
        for key in keys_list:
            result_asset = GuileService.GetKV(Class=AssetService.ASSETS_CLASS, key=str(key))
            asset_data = result_asset.get("answer", {})
            
            if asset_data and asset_data.get("ownerId") == user_id:
                user_assets.append({"id": key, "data": asset_data})
        
        if len(user_assets) > 0:
            return {"success": True, "assets": user_assets}
        
        return {"success": False, "error": f"No assets found for user {user_id}"}
        
        
    @staticmethod
    def list_all_assets() -> dict:
        """
        Recupera tutti gli asset dalla blockchain
        
        Returns:
            dict: Lista di tutti gli asset
        """
        result = GuileService.GetKeys(Class=AssetService.ASSETS_CLASS)
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False
        
        answer = result.get("answer", {})
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
        
        assets = []
        for key in keys_list:
            result_asset = GuileService.GetKV(Class=AssetService.ASSETS_CLASS, key=str(key))
            asset_data = result_asset.get("answer", {})
            
            if asset_data:
                assets.append({"id": key, "data": asset_data})
        
        if len(assets) > 0:
            return {"success": True, "assets": assets}
        
        return {"success": False, "error": f"No assets found"}

    @staticmethod
    def get_asset_history(asset_id: str) -> dict:
        """
        Recupera la storia di un asset (tutte le modifiche)
        
        Args:
            asset_id: ID dell'asset
            
        Returns:
            dict: Cronologia dell'asset
        """
        try:
            result = GuileService.GetKeyHistory(Class=AssetService.ASSETS_CLASS, key=str(asset_id))
            
            if "error" not in result:
                return {"success": True, "asset_id": asset_id, "history": result.get("answer", [])}
            else:
                return {"success": False, "error": result.get("error")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_asset_status(asset_id: str, new_status: AssetStatus) -> dict:
        """
        Aggiorna lo stato di un asset
        
        Args:
            asset_id: ID dell'asset
            new_status: Nuovo stato (active, sold, ecc.)
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Recupera l'asset attuale
        res = AssetService.get_asset(asset_id)
        
        if not res:
            return False
        
        if not res.get("success"):
            return res
        
        asset_data = res.get("data")
        
        # Aggiorna lo stato
        asset_data["status"] = new_status.value
        
        # Salva le modifiche
        result = GuileService.AddKV(Class=AssetService.ASSETS_CLASS, key=asset_id, value=asset_data)
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False
        
        return {"success": True, "asset_id": asset_id, "new_status": new_status}

    @staticmethod
    def update_asset_auction(asset_id: str, auction_id: str) -> dict:
        """
        Associa un'asta a un asset
        
        Args:
            asset_id: ID dell'asset
            auction_id: ID dell'asta
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Recupera l'asset attuale
        res = AssetService.get_asset(asset_id)
        
        if not res:
            return False
        
        if not res.get("success"):
            return res
        
        asset_data = res.get("data")
        
        # Aggiorna l'ID dell'asta
        asset_data["currentAuctionId"] = auction_id
        
        # Salva le modifiche
        result = GuileService.AddKV(Class=AssetService.ASSETS_CLASS, key=asset_id, value=asset_data)
        
        if "error" in result:
            current_app.logger.error(f"Error: {result.get("error")}")
            return False
        
        return {"success": True, "asset_id": asset_id, "auction_id": auction_id}

