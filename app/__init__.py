from flask_mail import Mail

from app.logging_config import setup_logging

import os
from dotenv import load_dotenv
from datetime import datetime
from email.utils import format_datetime

from flask import Flask, session, url_for, redirect
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

load_dotenv()

bcrypt = Bcrypt()
db = SQLAlchemy()
jwt = JWTManager()


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
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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

    app.jinja_env.filters["datetimeformat"] = format_datetime

    # Inizializzazione estensioni
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
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

    app.register_blueprint(frontend_bp, url_prefix="/")
    app.register_blueprint(api_auth, url_prefix="/api/v1/auth")
    app.register_blueprint(api_assets, url_prefix="/api/v1/")
    app.register_blueprint(api_auctions, url_prefix="/api/v1/")
    app.register_blueprint(api_bids, url_prefix="/api/v1/")
    app.register_blueprint(api_admin, url_prefix="/api/v1/admin")
    app.register_blueprint(api_admin_asset, url_prefix="/api/v1/admin")
    app.register_blueprint(api_admin_auctions, url_prefix="/api/v1/admin")

    # Database Upgrade automatico
    from flask_migrate import upgrade

    with app.app_context():
        try:
            upgrade()
            app.logger.info("Database migrato/aggiornato con successo!")
        except Exception as e:
            app.logger.error(f"Errore durante l'upgrade del database: {e}")

    return app
