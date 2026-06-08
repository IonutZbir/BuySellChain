from flask_mail import Mail

from app.logging_config import setup_logging

import os
from dotenv import load_dotenv
from datetime import datetime
from email.utils import format_datetime
from app.models.models import Messages
from flask import Flask, session, url_for, redirect
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

load_dotenv()

bcrypt = Bcrypt()
jwt = JWTManager()

from flask import request, jsonify
from app.services.log_services import LogService
from app.models.models import LogType
# Assicurati di importare jwt, che è l'istanza del tuo JWTManager, es: jwt = JWTManager(app)

def register_jwt_error_handlers(jwt):
    
    # 1. Token mancante (Missing Authorization Header)
    @jwt.unauthorized_loader
    def missing_authorization_header_callback(error_string):
        LogService.record_log(
            message=Messages.PREFIX_JWT_REQUIRED.value.format(endpoint=request.endpoint) + f"Header di autorizzazione mancante ({error_string})",
            level=LogType.ALERT,
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "-"),
            method=request.method,
        )
        return jsonify({
            "status": "fail", 
            "data": {"error": "Missing authorization header"}
        }), 401

    # 2. Token manipolato o firma non valida
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        LogService.record_log(
            message=Messages.PREFIX_JWT_REQUIRED.value.format(endpoint=request.endpoint) + f"Token JWT non valido o compromesso ({error_string})",
            level=LogType.ALERT, # Critico: qualcuno potrebbe star forgiando i token
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "-"),
            method=request.method,
        )
        return jsonify({
            "status": "fail", 
            "data": {"error": "Missing authorization header or invalid token"}
        }), 401

    # 3. Token scaduto (fisiologico, ma utile da loggare come INFO)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        LogService.record_log(
            message=Messages.PREFIX_JWT_REQUIRED.value.format(endpoint=request.endpoint) + "Accesso negato: Sessione JWT scaduta",
            level=LogType.INFO, 
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "-"),
            method=request.method,
        )
        return jsonify({
            "status": "fail", 
            "data": {"error": "Token has expired"}
        }), 401

@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    # This function runs automatically when an expired token is detected
    session.clear()
    return redirect(url_for("frontend.login"))


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
    except (TypeError, ValueError):
        return identity_str


def format_datetime(value, format="%d/%m/%Y %H:%M"):
    if value is None:
        return ""

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value

    return value.strftime(format)


def create_app():

    setup_logging(__name__)
    app = Flask(__name__)

    CORS(app)

    # Configurazione
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ALGORITHM"] = "HS256"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    app.config['AES_SECRET_KEY'] = os.getenv('AES_SECRET_KEY')
    app.config['OLLAMA_URL'] = os.getenv('OLLAMA_URL')
    app.config['OLLAMA_MODEL_NAME'] = os.getenv('OLLAMA_MODEL_NAME', 'qwen3.5')
    app.config['OLLAMA_REQUEST_TIMEOUT'] = int(os.getenv('OLLAMA_REQUEST_TIMEOUT', 60))
    app.jinja_env.filters["datetimeformat"] = format_datetime

    # Inizializzazione estensioni
    bcrypt.init_app(app)
    jwt.init_app(app)
    # Chiama la funzione per registrare i tuoi logger personalizzati
    register_jwt_error_handlers(jwt)
    mail = Mail(app)
    app.extensions['mail'] = mail  # Salva l'istanza di Mail nelle estensioni di Flask per poterla usare nei servizi

    # Blueprints
    from app.routes.admin.admin_asset.api_admin_asset import api_admin_asset
    from app.routes.admin.admin_auction.api_admin_auctions import api_admin_auctions
    from app.routes.assets.api_assets import api_assets
    from app.routes.auctions.api_auctions import api_auctions
    from app.routes.bids.api_bids import api_bids
    from app.routes.admin.api_admin import api_admin
    from app.routes.auth.api import api_auth
    from app.routes.frontend.routes import frontend_bp
    from app.routes.threat_analysis.api import api_ta
    from app.routes.test_ip import api_test_ip

    app.register_blueprint(frontend_bp, url_prefix="/")
    app.register_blueprint(api_ta, url_prefix="/api/v1/analyze")
    app.register_blueprint(api_auth, url_prefix="/api/v1/auth")
    app.register_blueprint(api_assets, url_prefix="/api/v1/")
    app.register_blueprint(api_auctions, url_prefix="/api/v1/")
    app.register_blueprint(api_bids, url_prefix="/api/v1/")
    app.register_blueprint(api_admin, url_prefix="/api/v1/admin")
    app.register_blueprint(api_admin_asset, url_prefix="/api/v1/admin")
    app.register_blueprint(api_admin_auctions, url_prefix="/api/v1/admin")
    app.register_blueprint(api_test_ip,url_prefix="/api/v1/")
    

    return app
