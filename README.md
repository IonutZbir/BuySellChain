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