"""
Modulo di routing frontend per la gestione delle pagine pubbliche dell'applicazione.
Contiene i percorsi per:
- Autenticazione (login e registrazione)
- Pagina principale
- Creazione di nuove aste con controllo d'accesso protetto
"""

from glob import glob
import os

from flask import Blueprint, current_app, redirect, render_template, session, url_for

from app.services.asset_services import AssetService
from app.services.auction_services import AuctionService

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/login")
def login():
    return render_template("login.html")


@frontend_bp.route("/signin")
def signin():
    return render_template("signin.html")


@frontend_bp.route("/faq")
def faq():
    return render_template("faq.html")


@frontend_bp.route("/dashboard")
def dashboard_page():
    if "user_id" not in session:
        return redirect(url_for("frontend.login"))

    user_role = session.get("role")
    user_id = session.get("user_id")

    if user_role == "admin":
        return render_template("admin.html")

    return render_template("dashboard.html", user_role=user_role, user_id=user_id)


@frontend_bp.route("/")
def index():
    session.pop("allowed_navigation", None)
    return render_template("index.html")


"""
Meccanismo di protezione per la pagina di creazione aste:
    L'accesso alla rotta /auctions/create è limitato e controllato attraverso un sistema
    di autorizzazione basato sulla sessione. Gli utenti possono accedere a questa pagina
    solo tramite il pulsante "crea asta" nella barra di navigazione.
    Flusso di controllo:
    1. L'utente clicca il pulsante "crea asta" nella navbar
    2. Viene effettuata una richiesta GET a /click-create-auction
    3. Il server verifica se l'utente è autenticato (presence di 'user_id' in session)
    4. Se l'utente è loggato, viene impostato il flag allowed_navigation in sessione
    5. L'utente viene reindirizzato a /auctions/create
    6. Il template viene renderizzato se il flag di autorizzazione è presente
    7. Se l'utente tenta di accedere direttamente a /auctions/create senza autorizzazione,
       viene reindirizzato alla pagina principale
    Nota: Il flag di autorizzazione viene eliminato quando l'utente naviga verso altre pagine
    per impedire accessi non autorizzati tramite refresh della pagina.
    Alternativa: L'autenticazione potrebbe essere gestita tramite JWT, ma richiederebbe
    l'implementazione di richieste POST anziché GET.
"""


@frontend_bp.route("/click-create-auction")
def click_create_auction():
    if "user_id" not in session:
        return redirect(url_for("frontend.login"))

    session["allowed_navigation"] = True
    return redirect(url_for("frontend.create_auction_page"))


@frontend_bp.route("/auctions/create")
def create_auction_page():
    if not session.get("allowed_navigation", None):
        return redirect(url_for("frontend.index"))

    return render_template("create_auction.html")


@frontend_bp.route("/auction/<auction_id>")
def show_asta(auction_id):
    current_user_id = session.get("user_id")
    data = AuctionService.get_auction(auction_id)
    auction = data.get("auction_data", {})

    high_bid_amount = auction.get("high_bid_amount", 0)
    if high_bid_amount is None:
        high_bid_amount = 0
    auction_data = {
        "auction_id": auction.get("id"),
        "asset_id": auction.get("asset_id"),
        "seller_id": auction.get("seller_id"),
        "start_time": auction.get("start_time"),
        "end_time": auction.get("end_time"),
        "starting_price": int(auction.get("starting_price", 0)),
        "min_incr": int(auction.get("min_incr", 0)),
        "status": auction.get("status"),
        "high_bid_amount": int(high_bid_amount),
        "bid_count": int(auction.get("bid_count", 0)),
    }

    # CARICHIAMO L'ASSET SEMPRE (indipendentemente dallo status)
    asset_response = AssetService.get_asset(auction.get("asset_id"))
    if asset_response and asset_response.get("success"):
        asset_data = asset_response.get("data", {}).get("value", {})
        auction_data["asset_title"] = asset_data.get("title", "Titolo non disponibile")
        auction_data["asset_description"] = asset_data.get("description", "")

        # Gestione Immagine
        asset_id = asset_data.get("id", "")
        owner_id = asset_data.get("owner_id", "")
        image_paths = glob(
            os.path.join(AssetService.base_upload_dir_absolute(), owner_id, asset_id, "primary-*.*")
        )

        if image_paths:
            filename = os.path.basename(image_paths[0])

            auction_data["image_url"] = os.path.join(
                AssetService.base_upload_dir_relative(),
                asset_data.get("owner_id", ""),
                asset_data.get("id", ""),
                filename,
            ).replace("\\", "/")
        else:
            auction_data["image_url"] = os.path.join(
                AssetService.base_upload_dir_relative(), "default.png"
            ).replace("\\", "/")
    else:
        auction_data["asset_title"] = "Asset non trovato"
        auction_data["asset_description"] = "Dettagli non disponibili."

    current_app.logger.info(
        f"Rendering auction page for auction_id={auction_id} with data: {auction_data}"
    )

    is_owner = bool(current_user_id and auction_data.get("seller_id") == current_user_id)

    return render_template("auction.html", auction_data=auction_data, is_owner=is_owner)
