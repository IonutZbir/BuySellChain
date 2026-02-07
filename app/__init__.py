from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app) # Permette al frontend di chiamare l'API

    from app.routes.auth.api import api_auth
    app.register_blueprint(api_auth, url_prefix='/api/v1/auth')

    return app