# Progetto Cybersecurity

## Struttura Progetto

```
app/            
├── __init__.py # Inizializzazione del pacchetto app
├── middleware/
├── models/     # Modelli del database
├── routes/     # Blueprint e rotte dell'applicazione
│   ├── admin/  # Rotte per l'area amministrativa
│   ├── frontend/   # Frontend routes
│   └── auth/   # Rotte per l'autenticazione
├── services/   # Logica di business e servizi ausiliari
├── static/     # File statici (CSS, JS, immagini)
│   ├── css/
│   └── js/
├── templates/  # Template HTML (Jinja2)
migrations/
```

## Migrazione db

Per la prima volta, eseguire `flask db init`, poi:

1. `flask db migrate -m 'desc'`
2. `flask db upgrade`

Comando per entrare nel docker (per DB) `docker exec -it postgres_db psql -U user_bsc -d buysellchain`


**Per eseguire l'app** `flask run --debug` (per il debug), oppure `python3 run.py`

**Per eseguire l'app in `https`** `flask run --devy`

## Docker PSQL

Per eseguire il docker con psql: `docker-compose up -d`.

Per fermare il container: `docker-compose down` oppure `docker-compose stop`.

Per cancellare tutto, sia container che dati: `docker-compose down -v`

Quando si deve fare una migrazione, in locale eseguire i passaggi precedenti, poi lanciare il docker con PSQL, ci penserà poi python ad aggiorane la struttura del db.

## Generazione chiavi segrete

```python
import secrets
sk = secrets.token_hex(32)
```

## Note

post registrazione, email di conferma

Per essere venditore, l utente si deve registrare come venditore (ad esempio aggiunge il codice fiscale)
piu avanti, inviare email all admin per accettazione

## frontend
/ - una lista delle aste (layout GRID) con la foto in primo piano, cliccando sopra, accede alla pagina dell'asta, dove puo decidere se partecipare o meno
/profile dati personali - ci si pensa piu in la
/auction -> Form... Non ci sono immobili da vendere? -> pop up con form per registrare immobile
/auction/id_asta/ da questa pagina, l utente puo fare offerte (se l utente che accede è l utente che l ha creata, vede le statistiche)

## Modifiche fatte oggi - 14/02/2026

- Aggiunta BLockChainID (email+uuid) in JWT
- Creata route asset/user -> ritorna tutti gli asset dell'utente `user` trovato tramite JWT in request
- sistemazione form crea asta e crea asset con popup (modifca queindi dei file .js associati)
- fetch aste su index.html

## Modifiche fatte oggi - 17/02/2026 - Franco
- Aggiunta model per Auction e Bid
- modifica api_asset,auction e bid
- creati i services (vedi che cazzo è uscito fuori per le funzioni, sopratutto le bid che sono ancora da sistemare)
- creati i bck passati delle api (nse sa mai)
- Problemi (avendo cambiato la forma delle richieste/risposte in jsend, andrebbe riaddattato tutto)
    - index.js recuperare le aste da frontend
    - create auctions.js recupero asset

Mancano la validazione delle aste con asset, cioò bloccare la creazione dell'asta se un'asset è stato già usato. (da capire come);
lavorare ancora su bid, anche con jwt

## Modifiche fatte oggi 18/02/2026 - Ionut/Franco
- Sistemato registrazione, ora non va piu al login quando "crea asta"
- Definito formato dei dati per le risposte (jsend.py)
- Presentazione aste su index.html

## Modifiche fatte oggi 20/02/2026 - Ionut

- Frontend: nella pagina auctions/create, aggiunta di un bottone per creare asset + aggiunta upload immagine
- Backend: gestione upload immagine. Le immagini vengono caricate in: `static/assets/{owner_id}/{asset_id}/`. L'immagine principale è salvata come `primary-uuid().ext`, mentre le altre come verranno salvate come `uuid().ext`

- Modificato `list_auctions().py` (`/routs/auctions`). Nella risposta, definiamo da 0 il dizionario `response_data`, nel quale includere i dati richiesti. Modficato adeguatamente anche il frontend.

## Modifiche fatte oggi 27/02/2026 - Ionut

- Frontend: aggiunta pagina `/faq` nella quale andremo a spiegare come funziona la piattaforma. Modificato anche il footer. Validazione dati creazione asta. Aggiunta la possibilità di creare un account `Venditore`. Modificata pagina di creazione aste/asset
- Backend: Modificato /auth/api.py implementando la registrazione di un utente `Seller`.
- Databse: Modificata la tabella user. Eseguire il "flask db upgrade" dopo aver riavviato il container.

- Sistemare e centrallizzare le api (Franco)
- Implementare singole pagine per ciascuna asta (Ionut)
- Modificare i JSON delle rispsote pe semplificando il formato (anche centralizzare il sistema di creazione delle risposte) (Ionut/Franco)
- Implemetnare sistema registrazione seller + ruoli (Ionut)

## Modifiche fatte il giorno 4/03/2026 - Franco

- Backend:
* aggiunta invio offerte a BC correttamente
* aggiunta validazione offere con status e reason
* aggiunta recupero ultima offerta valida con relativo amount
* TODO : Modificare generazione id per Modelli da sha256 a HMAC, ragionare su short url (idea: ripemod di HMAC id asta)
* TODO : Refactor di commenti e print di debug (da fare alla fine)
- Frontend:
* modifica pagina "partecipa ad asta"

TODO: prossimo aggiornamento, fare asta attiva per un tot di ore (es: 8.00 - 20.00), poi da fine a inizio asta in stato locked -> stato lock = blocco invio offerte e calcolo e visualiazzione high_bid_amount (parziale)

## Modifiche fatte il giorno 11/03/2026 - Ionut

- Creazione di Id usando HMAC
- Logger funzionante con colori per vari livelli piu scrittura su file

TODO: Se il token jwt è expired gestire errore e rimandare al frontend.
TODO: Generare le chiavi in modo sicuro.
TODO: Finire le aste, aggiungere il lock temporale

## Modifiche fatte il giorno 14/03/2026 - Ionut

- Frontend: L'unico dettaglio temporale che il venditore puo definire è l'inizio e la fine dell'asta. Nella pagina di creazione asta, ho aggiunto quell'aside nel quale scrivere le informazioni su come funziona l'asta e la sua durata.
- Backend: Quando viene effettuata una bid, viene effettuato un controllo per verificare se l'offerta è stata effettuata entro le 8 (n) ore a disposizione. Le ore le ho definite in una costante. Aggiunta una route in api_bids `get_allowed_bid_timeframe` per poter creare un timer da frontend nella pagina dell'asta. Inoltre ora il bottone per inviare offerte è renderizzato solo se bidderId != sellerId
- Creata pagina dashboard per l'admin, per ora per creare un admin lo si fa direttamente da psql.
- Dashboard utente "seller" e "bidder"

TODO: Fare un ultimo check per assigurarci che tutto funziona come dovrebbe funzionare. Rivedere alcuni dettagli a livello frontend. Creare una routine che aggiorna automaticamente lo stato delle aste sulla blockchain.

## Modifiche fatte il giorno 17/03/2026 - Franco

- Frontend: 
    - modifiche grafiche alla pagina dell'asta in base a chi sta guardando (seller, bidder)
    - modifiche alla dashboard
- Backend:
    - implementata logica di chiusura asta e ottenimento vincitore
    - implementata logica per invio email al vincitore + email in fase di registrazione seller + creazione `email_service`
    - implementata logica per impostare lo status dell'asta in base al tempo trascorso con aggiunta delle route `auctions/active/auction_id`, `auctions/lock/auction_id` e `auctions/close/auction_id`
    - aggiunta della route `bids/total/auction_id` per recupero offerte totali di specifica asta

Modifiche e sistemazione della gestione dei range temporali per asta
TODO: fare check finale + routine aggiornamento status aste

## Modifiche fatte il giorno 02/04/2026 - Franco & Ionut

Aggiunta tracciamento delle offerte (storico offerte con GetKeyHistory)
Modifche ai layout pagina aste
Modifiche lato backend alle api (bids, auctions)

TODO : Aggiungere refresh pagine con polling