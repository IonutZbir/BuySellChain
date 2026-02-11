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
