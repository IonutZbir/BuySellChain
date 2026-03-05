import logging
import uuid

from flask import current_app
from app.models.models import Asset, AssetStatus, AssetType
from app.services.guile_services import GuileService
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger()


class AssetService:
    """Servizio per gestire gli asset sulla blockchain"""

    ASSETS_CLASS = "Assets"

    @staticmethod
    def create_asset(owner_id: str, title: str, description: str, asset_type: AssetType, 
                    size: float, price: float, location: str, picture=None) -> dict:
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
        
        asset = Asset(owner_id, title, description, asset_type, size, price, location, picture)
        
        logger.info(f"Created asset: {asset}")  # Debug print
        # Salva l'asset sulla blockchain via Guile
        logger.info(f"Saving asset to blockchain with ID: {asset.get_id()}")  # Debug print
        logger.info(f"Asset data to save: {asset.to_json()}")  # Debug print
        result = GuileService.AddKV(Class=AssetService.ASSETS_CLASS, key=asset.get_id(), value=asset.to_json())
        logger.info(f"Result from Guile AddKV: {result}")  # Debug print
        if "error" in result:
            logger.error("Error: {}".format(result.get('error')))
            return False

        if not AssetService._upload_picture(owner_id, asset.get_id(), asset.picture):
            logger.info(f"Failed to upload picture for asset ID: {asset.get_id()}")
            return False

        logger.info(f"Asset created and picture uploaded successfully for asset ID: {asset.get_id()}")
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
            logger.error("Error: {}".format(result.get('error')))
            return False
        
        if result.get("answer") is not False and result.get("answer"):
            asset_data = result.get("answer", {})
            return {"success": True, "data": asset_data}
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
        logger.debug(f"Result from Guile GetKeys: {result}")
        print("Result from Guile GetKeys:", result)  # Debug print
        if "error" in result:
            logger.error("Error: {}".format(result.get('error')))
            return False
        
        answer = result.get("answer", {})
        logger.debug(f"Answer from GetKeys: {answer}")
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
        
        user_assets = []
        for key in keys_list:
            logger.debug(f"Checking asset key: {key} for user {user_id}")  # Debug print
            result_asset = GuileService.GetKV(Class=AssetService.ASSETS_CLASS, key=str(key))
            asset_data = result_asset.get("answer", {}).get("value", {})
            logger.debug(f"Asset data for key {key}: {asset_data}")  # Debug print
            if asset_data.get("owner_id") == user_id:
                user_assets.append({"id": key, "value": asset_data})
        
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
            logger.error("Error: {}".format(result.get('error')))
            return False
        
        answer = result.get("answer", {})
        keys_list = [key[0] if isinstance(key, list) else key for key in answer.get("keys", [])]
        
        logger.debug(f"Assets recuperati: {answer}")
        
        assets = []
        for key in keys_list:
            result_asset = GuileService.GetKV(Class=AssetService.ASSETS_CLASS, key=str(key))
            asset_data = result_asset.get("answer", {})
            
            if asset_data:
                assets.append({"asset_data": asset_data})
        
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
            logger.error("Error: {}".format(result.get('error')))
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
            logger.error("Error: {}".format(result.get('error')))
            return False
        
        return {"success": True, "asset_id": asset_id, "auction_id": auction_id}


    def _upload_picture(owner_id: str, asset_id: str, picture) -> str:
        # 1. Definiamo la cartella base
        # static/uploads
        base_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        
        # assets/1/101/primary-uuid().jpg
        ext = os.path.splitext(secure_filename(picture.filename))[1] # Prende l'estensione (.jpg, .png)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        relative_path = os.path.join('assets', str(owner_id), str(asset_id), f"primary-{unique_filename}")
        
        # 3. Percorso assoluto per il sistema operativo
        absolute_filepath = os.path.join(base_upload_dir, relative_path)
        
        try:
            # Crea le cartelle (static/uploads/assets/owner/asset/)
            os.makedirs(os.path.dirname(absolute_filepath), exist_ok=True)
            
            # Salva il file
            picture.save(absolute_filepath)
            
            # Restituisci il percorso relativo (in futoro potremmo voler salvare questo percorso sulla blockchain)
            return relative_path
            
        except Exception as e:
            current_app.logger.error(f"Errore upload: {e}")
            return False
    
    def base_upload_dir_absolute():
        return os.path.join(current_app.root_path, 'static', 'uploads', 'assets')
    
    def base_upload_dir_relative():
        return os.path.join("/", 'static', 'uploads', 'assets')
