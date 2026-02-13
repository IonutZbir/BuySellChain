"""
Modulo di routing frontend per la gestione delle pagine pubbliche dell'applicazione.
Contiene i percorsi per:
- Autenticazione (login e registrazione)
- Pagina principale
- Creazione di nuove aste con controllo d'accesso protetto
"""

from flask import Blueprint, abort, flash, redirect, render_template, session, url_for

from flask_jwt_extended import jwt_required

from app.routes.auctions.api_auctions import list_auctions_by_status

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/login')
def login():
    return render_template('login.html')

@frontend_bp.route('/signin')
def signin():
    return render_template('signin.html')


@frontend_bp.route('/')
def index():
    session.pop('allowed_navigation', None)
    return render_template('index.html')

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

@frontend_bp.route('/click-create-auction')
def click_create_auction():
    if 'user_id' not in session:
        return redirect(url_for('frontend.login'))
    
    session['allowed_navigation'] = True
    return redirect(url_for('frontend.create_auction_page'))

@frontend_bp.route('/auctions/create')
def create_auction_page():
    if not session.get('allowed_navigation', None):
        return redirect(url_for('frontend.index'))
    
    return render_template('create_auction.html')


# @frontend_bp.route('/auction/{auction_id}')
# def show_asta():
#     data = list_auctions_by_status(id)
#     render_template('auction.html', params=data)