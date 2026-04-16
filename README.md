# Progetto Cybersecurity

## Struttura Progetto

```bash
BuySellChain/
├── app/
│   ├── __init__.py                 # Inizializzazione del pacchetto app
│   ├── middleware/
│   │   └── auth.py                 # Middleware autenticazione JWT
│   ├── models/                     # Modelli del database SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py                 # Modello User
│   │   ├── asset.py                # Modello Asset
│   │   ├── auction.py              # Modello Auction
│   │   └── bid.py                  # Modello Bid
│   ├── routes/                     # Blueprint e rotte dell'applicazione
│   │   ├── __init__.py
│   │   ├── admin/                  # Rotte per l'area amministrativa
│   │   │   └── api.py
│   │   ├── frontend/               # Frontend routes
│   │   │   └── pages.py
│   │   └── api/                    # API REST routes
│   │       ├── auth.py             # Autenticazione e profilo
│   │       ├── assets.py           # Gestione asset
│   │       ├── auctions.py         # Gestione aste
│   │       └── bids.py             # Gestione offerte
│   ├── services/                   # Logica di business
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── asset_service.py
│   │   ├── auction_service.py
│   │   ├── bid_service.py
│   │   ├── blockchain_service.py
│   │   └── email_service.py
│   ├── static/                     # File statici
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/                 # Immagini asset utenti
│   ├── templates/                  # Template HTML Jinja2
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/
│   │   ├── auctions/
│   │   ├── dashboard/
│   │   └── profile.html
│   └── utils/
│       ├── logger.py
│       └── jsend.py
├── migrations/                     # Migrazioni database Alembic
├── config.py                       # Configurazione applicazione
├── run.py                          # Entry point applicazione
├── requirements.txt
└── .env                            # Variabili ambiente
```

## Setup e Configurazione

### Migrazione Database

Per la prima volta, eseguire `flask db init`, quindi:

1. `flask db migrate -m 'description'`
2. `flask db upgrade`

### Esecuzione dell'Applicazione

```bash
# Modalità debug
flask run --debug

# Modalità produzione
python3 run.py

# Con HTTPS
flask run --devy
```

### Docker PostgreSQL

```bash
# Avviare il container
docker-compose up -d

# Fermare il container
docker-compose stop

# Fermare e rimuovere tutto (inclusi i dati)
docker-compose down -v
```

**Accedere al database:**

```bash
docker exec -it postgres_db psql -U user_bsc -d buysellchain
```

**Nota:** Durante le migrazioni, eseguire i comandi locali, quindi avviare il container Docker. Python aggiornerà automaticamente la struttura del database.

### Generazione Chiavi Segrete

```python
import secrets
sk = secrets.token_hex(32)
```

## Log delle Modifiche

### 14/02/2026

- Aggiunta BlockChainID (email+uuid) in JWT
- Creata route `asset/user` per recuperare asset dell'utente autenticato
- Sistemazione form creazione asta e asset con popup
- Implementato fetch aste su index.html

### 17/02/2026 - Franco

- Aggiunta model Auction e Bid
- Modifica API asset, auction, bid
- Creati service layer per logica di business
- Backup API implementati
- **TODO:** Adattare risposte al nuovo formato jsend; validare asset in aste; sistemare logica bid con JWT

### 18/02/2026 - Ionut & Franco

- Corretto flusso registrazione
- Definito formato risposte standardizzato (jsend.py)
- Implementata presentazione aste su index.html

### 20/02/2026 - Ionut

- Upload immagine asset con struttura `static/assets/{owner_id}/{asset_id}/`
- Gestione immagine primaria e secondarie
- Refactor `list_auctions()` con risposta strutturata
- **TODO:** Centralizzare API; singole pagine per asta; semplificare JSON

### 27/02/2026 - Ionut

- Aggiunta pagina FAQ
- Registrazione utenti Seller con ruoli
- Validazione creazione asta
- Modifica tabella user (eseguire `flask db upgrade`)
- **TODO:** Implementare pagine singole aste; sistema registrazione seller avanzato

### 04/03/2026 - Franco

- Invio offerte a blockchain
- Validazione offerte con status e reason
- Recupero ultima offerta valida
- **TODO:** Refactor ID con HMAC; sistemare debug; implementare stato asta temporale

### 11/03/2026 - Ionut

- Generazione ID con HMAC
- Logger con colori e scrittura su file
- **TODO:** Gestire JWT expired; chiavi sicure; lock temporale aste

### 14/03/2026 - Ionut

- Controllo timeframe offerte (8 ore configurabili)
- Route `get_allowed_bid_timeframe` per timer frontend
- Dashboard admin, seller, bidder
- Renderizzazione bottone offerta condizionata (bidderId ≠ sellerId)
- **TODO:** Verifiche finali; dettagli frontend; routine aggiornamento stato aste

### 17/03/2026 - Franco

- Chiusura asta e determinazione vincitore
- Email service: notifiche vincitore, registrazione seller, partecipanti
- Route stato asta: `active`, `lock`, `close`
- Route `bids/total/{auction_id}`
- **TODO:** Check finale; routine auto-aggiornamento status

### 02/04/2026 - Franco & Ionut

- Tracciamento storico offerte con GetKeyHistory
- Refactor layout pagine aste e API
- **TODO:** Polling refresh pagine

### 07/04/2026 - Franco

- Filtro storico offerte per ruolo e stato asta (seller vede tutto; bidder vede filtrato)
- Counter offerte live in pagina asta e dashboard
- Email post-chiusura con motivazioni personalizzate
- Sezione Profile autenticata con GET/PUT `/api/v1/auth/profile`
- Query SQLAlchemy con validazioni email, telefono, codice fiscale

# Progetto Cybersecurity - 2

L'idea è di estendere la piattaforma, implementando anche un sistema *finanziario*, o definendo una nostra crypto (oppure usandone una già esistente *meglio*). In questo modo possiamo autenticare gli utenti con il wallet, o implemendo un wallet da 0 o usandone uno già esistente (`estensione browser`).

1. Autenticazione su blockchain. Se consideriamo di estenderla usando una crypto currency (BTC, ETH, qualsiasi altra), l'autenticazione la possiamo gestire con il wallet della cryptocurrency scelta, Mantenendo nella nostra blockchain la chiave pubblica del utente. Estendere il sistema rendendolo distribuito, ciascun venditore/compratore dovrà scaricarsi la blockchain in locale. Questo ci permette di eliminare la `centralizzazione del Server Gateway`, togliendo anche la necessità di avere `admin di sistema`.
2. Tabella Alert-Log
3. Modificare la documentazione, definendo bene il threat model del nostro sistem. Rendendolo distribuito, ora abbiamo degli asset da aggiungere.
