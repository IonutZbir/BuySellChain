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

## Init modifiche parte 2

- Definire **baseline**, **deviazioni** e **contromisure** -> diretto su doc

- Definire campi dei log e cifrare campi sensibili
- Sistemare livelli dei log
- Definire cosa scrivere su blockchain e cosa lasciare su file


## Eserctiazione Threat Model

- Asset: Docuementi critici degli utenti, un riconoscitore che legge dei badge (?? Zona Field). Certificazione tramite ente esterno dell'esistenza degli immobili. Verificare che realmente le case sono messe in vendità. Considerare il catasto `https://catastomappe.it/api_catasto`.

Mettere contenuto Profile dentro dashboard, solo nome e cognome utente


# LogService

formato:
- timestamp di quando avviene la richiesta
- from ip (cifrato)
- livello criticità (ALERT, INFO)
- metodo (es. GET, POST)
- msg (no msg ambigui/con troppe info)
- user_agent

Da loggare su BL:
- quando avviene login e registrazione user
- creazione asta
- creazione asset
- invio offerte effettuate


- Aggiungere campo payoad size
- definire delle api per accedere ai log come admin
- aggiungere id utente, asset, asta, offerta quando inserita nella blockchain

**Esempio Log da API**
```
"data": {
        "logs": [
            {
                "created_at": "2026-05-15T11:47:53.512788",
                "from_ip": "127.0.0.1",
                "id": "6a8e249114664e905f84d83d7c992a860e950f5baf04894679581a05bd69d9e1",
                "level": "INFO",
                "message": "Nuovo utente registrato",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
            }
        ]
    },
"status": "success"
```

**Stesso Esempio ma da GetKV**
```
{
    "success": true,
    "message": "Ok",
    "answer": {
        "value": {
            "id": "6a8e249114664e905f84d83d7c992a860e950f5baf04894679581a05bd69d9e1",
            "description": "Nuovo utente registrato",
            "created_at": "2026-05-15T11:47:53.512788",
            "level": "INFO",
            "from_ip": "lIBpH+5m+OHAsrUVwVV1l9i0Yvu2KSqVGk8zxymgJpVQqOFKP70dRgg=",
            "user_agent": "2j0pqAPMUAad5KVGvUzR8gc9ZhmmWz3uYKvFNLeMaCe0mSQeuoY9ykcAcUAIenUC4xX/qShoxtY44qW5O00lRvxQM+zlcsGzkyxLxAhur5JX52232UPxn0DlWBjBY22ZU2XownYE",
            "method": "POST"
        },
        "key": [
            "6a8e249114664e905f84d83d7c992a860e950f5baf04894679581a05bd69d9e1"
        ],
        "class": "Logs"
    }
}
```

# Loggin Session

```
{
    "data": {
        "logs": [
            {
                "created_at": "2026-05-15T12:41:24.896036",
                "from_ip": "127.0.0.1",
                "id": "9f1b99fc04ee6a489da4901ab9eb226cfdbf930877f7422752c21a609a7d581a",
                "level": "ALERT",
                "message": "Accesso non autorizzato /auctions/create",
                "method": "GET",
                "user_agent": "curl/8.15.0"
            },
            {
                "created_at": "2026-05-15T12:35:00.391180",
                "from_ip": "127.0.0.1",
                "id": "d44f5dcabb1f6d678ee5e0d2f89db117ec409a8e31259fc99d31f1c322a36a57",
                "level": "ALERT",
                "message": "Accesso non autorizzato /assets POST",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            },
            {
                "created_at": "2026-05-15T12:33:42.144222",
                "from_ip": "127.0.0.1",
                "id": "c82cb1c7ceb5243b73ea93a5a43f97898f280d7e3e740b6752b36d3cb1f8022c",
                "level": "INFO",
                "message": "Nuovo utente registrato",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            },
            {
                "created_at": "2026-05-15T12:27:17.482174",
                "from_ip": "127.0.0.1",
                "id": "34ffbc9f9214358f44690465e7a4a0940c2cea55d04888a33ed867bab3ecb98d",
                "level": "INFO",
                "message": "Accesso riuscito",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            },
            {
                "created_at": "2026-05-15T12:14:15.482957",
                "from_ip": "127.0.0.1",
                "id": "c7c01050949504bb6eee58cdaefa460c7c4ba37d47f416dc881ce79e7a7a8791",
                "level": "INFO",
                "message": "Accesso a route admin ->/logs",
                "method": "GET",
                "user_agent": "PostmanRuntime/7.49.1"
            },
            {
                "created_at": "2026-05-15T12:13:43.605970",
                "from_ip": "127.0.0.1",
                "id": "f40310a42a01888922e71c4f4a5e7f10eff7210c5aed5837b3037718546a1f7a",
                "level": "INFO",
                "message": "Accesso a route admin ->/logs",
                "method": "GET",
                "user_agent": "PostmanRuntime/7.49.1"
            },
            {
                "created_at": "2026-05-15T12:13:11.931754",
                "from_ip": "127.0.0.1",
                "id": "73fd08fcf43f93c8e03a5761ac7352ca6561f6c1992b1bd570065515a6fc5101",
                "level": "INFO",
                "message": "Accesso a route admin ->/logs",
                "method": "GET",
                "user_agent": "PostmanRuntime/7.49.1"
            },
            {
                "created_at": "2026-05-15T12:13:08.651665",
                "from_ip": "127.0.0.1",
                "id": "bbebb6d67fdd1886ae6a9a3e48df56e9784cff3b346ccd00620d43b7a9de56c5",
                "level": "ALERT",
                "message": "Accesso non autorizzato/auctions/create",
                "method": "GET",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
            },
            {
                "created_at": "2026-05-15T12:12:50.066125",
                "from_ip": "127.0.0.1",
                "id": "64249809d3fcec6bec1f5d6e173d2ea1888e7c88c0579e232925a50ccbf30e77",
                "level": "INFO",
                "message": "Accesso a route admin ->/logs",
                "method": "GET",
                "user_agent": "PostmanRuntime/7.49.1"
            },
            {
                "created_at": "2026-05-15T12:12:46.858909",
                "from_ip": "127.0.0.1",
                "id": "2dc53a7dc4cd5f492dabb7d89c4a5c42ee276b21b569006268350ba226f3b666",
                "level": "INFO",
                "message": "Accesso riuscito",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
            },
            {
                "created_at": "2026-05-15T12:12:00.374480",
                "from_ip": "127.0.0.1",
                "id": "6435ba6d5e8a1ec0b2741c31be307bdd073aeeaa0a6c94dcf810cb1799bef8e8",
                "level": "INFO",
                "message": "Accesso riuscito",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
            },
            {
                "created_at": "2026-05-15T11:47:53.512788",
                "from_ip": "127.0.0.1",
                "id": "6a8e249114664e905f84d83d7c992a860e950f5baf04894679581a05bd69d9e1",
                "level": "INFO",
                "message": "Nuovo utente registrato",
                "method": "POST",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0"
            }
        ]
    },
    "status": "success"
}
```