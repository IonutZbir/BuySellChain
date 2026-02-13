from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from logging.config import dictConfig
from flask_jwt_extended import JWTManager
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# 1. Configurazione Logging (Prima di tutto)
dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'app.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 5,
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi', 'file']
    }
})

bcrypt = Bcrypt()
db = SQLAlchemy()
jwt = JWTManager()

# Queste callback servono a poter passare dizionare come identità degli utenti.
@jwt.user_identity_loader
def user_identity_lookup(user_data):
    import json
    if isinstance(user_data, dict):
        return json.dumps(user_data)
    return str(user_data)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    import json
    identity_str = jwt_data["sub"]
    try:
        return json.loads(identity_str)
    except (_jwt_header, ValueError):
        return identity_str

from .middleware.logger import register_logger_middleware


def create_app():
    app = Flask(__name__)
    
    # Forza il livello del logger di Flask a DEBUG per vedere i tuoi log
    app.logger.setLevel(logging.DEBUG)
    
    CORS(app) 
    
    # Configuration
    # .env PSQLURL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_SECRET_KEY"] = "super-secret" # da modificare
    
    app.config["JWT_ALGORITHM"] = "HS256"
    
    # DA MODIFICARE SERVE PER LA SESSIONE
    app.secret_key = 'una_chiave_temporanea_molto_segreta' # <--- Aggiungi questa
    
    # Rimuove l'errore 422 assicurando che la gestione dell'identità sia flessibile
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]

    # Inizializzazione estensioni
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    Migrate(app, db)
    # db.create_all()  # Rimuovi questa linea e usa `flask db upgrade` da CLI
    
    # Middleware
    register_logger_middleware(app) 
    
    # Blueprints
    from app.routes.admin.admin_asset.api_admin_asset import api_admin_asset
    from app.routes.admin.admin_auction.api_admin_auctions import api_admin_auctions
    from app.routes.assets.api_assets import api_assets
    from app.routes.auctions.api_auctions import api_auctions
    from app.routes.bids.api_bids import api_bids
    from app.routes.admin.api_admin import api_admin
    from app.routes.auth.api import api_auth
    from app.routes.frontend.routes import frontend_bp

    app.register_blueprint(frontend_bp, url_prefix="/")
    app.register_blueprint(api_auth, url_prefix='/api/v1/auth')
    app.register_blueprint(api_assets, url_prefix='/api/v1/')
    app.register_blueprint(api_auctions, url_prefix='/api/v1/')
    app.register_blueprint(api_bids, url_prefix='/api/v1/')
    app.register_blueprint(api_admin, url_prefix='/api/v1/admin/')
    app.register_blueprint(api_admin_asset, url_prefix='/api/v1/admin/')
    app.register_blueprint(api_admin_auctions, url_prefix='/api/v1/admin/')

    # Import modelli per Migrate
    from app.models.models import User
    
    from flask_migrate import upgrade
    with app.app_context():
        try:
            upgrade()
            app.logger.info("Database migrato/aggiornato con successo!")
        except Exception as e:
            app.logger.error(f"Errore durante l'upgrade del database: {e}")
    
    return app