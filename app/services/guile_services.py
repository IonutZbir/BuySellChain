# app/services/guile_service.py
import requests
from dotenv import load_dotenv
import os

###
# Questo servizio si occupa di comunicare con il CLI di Guile
# tramite HTTP. In questo modo, il backend Flask può inviare comandi al CLI
# e ricevere risposte, permettendo una comunicazione fluida tra i due componenti.

# ----- Modificare poi le funzioni 
###
load_dotenv()
class GuileService:
    @staticmethod
    def AddKV(Class, key, value=None):
        payload = {
            "cmd": "AddKV",
            "class": Class,
            "key": key,
            "value": value
        }
        try:
            # L'URL di Guile è definito nel file config.py
            #response = requests.post(current_app.config['GUILE_BRIDGE_URL'], json=payload)
            response = requests.post(os.getenv("GUILE_BRIDGE_URL"), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    @staticmethod
    def GetKV(Class, key):
        payload = {
            "cmd": "GetKV",
            "class": Class,
            "key": key
        }
        try:
            # L'URL di Guile è definito nel file config.py
            #response = requests.post(current_app.config['GUILE_BRIDGE_URL'], json=payload)
            response = requests.post(os.getenv("GUILE_BRIDGE_URL"), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    @staticmethod
    def GetKeys(Class):
        payload = {
            "cmd": "GetKeys",
            "class": Class,
            "key": []
        }
        try:
            response = requests.post(os.getenv("GUILE_BRIDGE_URL"), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    @staticmethod
    def GetKeyHistory(key, Class):
        payload = {
            "cmd": "GetKeyHistory",
            "class": Class,
            "key": key
        }
        try:
            # L'URL di Guile è definito nel file config.py
            #response = requests.post(current_app.config['GUILE_BRIDGE_URL'], json=payload)
            response = requests.post(os.getenv("GUILE_BRIDGE_URL"), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    @staticmethod
    def GetNumKeys(Class,key=None):
        payload = {
            "cmd": "GetNumKeys",
            "class": Class,
            "key":[]
        }
        try:
            # L'URL di Guile è definito nel file config.py
            #response = requests.post(current_app.config['GUILE_BRIDGE_URL'], json=payload)
            response = requests.post(os.getenv("GUILE_BRIDGE_URL"), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    