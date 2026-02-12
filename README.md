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

**Per eseguire l'app, eseguire** `flask run --debug` (per il debug), oppure `python3 run.py`

## Docker PSQL

Per eseguire il docker con psql: `docker-compose up -d`.

Per fermare il container: `docker-compose down` oppure `docker-compose stop`.

Per cancellare tutto, sia container che dati: `docker-compose down -v`

Quando si deve fare una migrazione, in locale eseguire i passaggi precedenti, poi lanciare il docker con PSQL, ci penserà poi python ad aggiorane la struttura del db.

## Note

post registrazione, email di conferma

Per essere venditore, l utente si deve registrare come venditore (ad esempio aggiunge il codice fiscale)
piu avanti, inviare email all admin per accettazione


ionut: documento - .yaml psql - generazione chiave segreta - dati di test - pulire requiments.txt
franco: api


## frontend
/ - una lista delle aste (layout GRID) con la foto in primo piano, cliccando sopra, accede alla pagina dell'asta, dove puo decidere se partecipare o meno
/profile dati personali - ci si pensa piu in la
/auction -> Form... Non ci sono immobili da vendere? -> pop up con form per registrare immobile
/auction/id_asta/ da questa pagina, l utente puo fare offerte (se l utente che accede è l utente che l ha creata, vede le statistiche)