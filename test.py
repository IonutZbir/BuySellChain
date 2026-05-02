import requests

richiesta = requests.get("http://localhost:5000/api/v1/whoami")
print(richiesta.json())