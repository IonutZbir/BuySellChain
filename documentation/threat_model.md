# Threat Model

## Logger

È stato implementato un sistema di logging, che scrive su blockchain gli eventi più importanti, quali l'accesso al sistema di un utente, la registrazione di asset/aste/offerte e tentativi di accesso a route non autorizzate.

La struttura dei record salvati in blockchain dal logger è la seguente:

```json
{

    "id": hash(description, created_at, level, from_ip, user_agent, method),
    "description": MessaggeType,
    "created_at": timestamp,
    "level": INFO/ALERT,
    "from_ip": source IPv4,
    "method": HTTTP method,
    "user_agent": client,
}
```

