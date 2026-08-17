# Trading Assistant V2.6

## Neu
- Supabase-Anbindung für **dauerhafte Speicherung**
- Depot und Watchlist bleiben nach Neustarts/Deployments erhalten
- Turbos und deren Basiswerte bleiben erhalten
- Fallback ohne Supabase: App läuft weiterhin, aber Änderungen sind nicht dauerhaft
- **Hype Radar Schnellüberblick direkt oben im Dashboard**
- vollständiger Hype-Radar-Reiter bleibt zusätzlich bestehen
- deutsche RSS-News für Aktien und Turbo-Basiswerte bleiben erhalten

## Warum Supabase?
Streamlit `session_state` ist nicht als dauerhafte Datenbank gedacht. Supabase stellt eine echte Postgres-Datenbank bereit und hat einen offiziellen Python-Client.

## Zusätzliche Streamlit Secrets

```toml
SUPABASE_URL = "https://DEIN-PROJEKT.supabase.co"
SUPABASE_SECRET_KEY = "DEIN_SUPABASE_SECRET_KEY"
```

**Wichtig:** Den Secret Key niemals in GitHub eintragen oder an andere Personen weitergeben. Er wird nur serverseitig von Streamlit verwendet.

## Einrichtung
1. Kostenloses Supabase-Projekt anlegen.
2. `supabase_setup.sql` aus diesem Paket im Supabase SQL Editor ausführen.
3. Projekt-URL und Secret Key in Streamlit unter **Settings → Secrets** ergänzen.
4. App neu starten.
5. In der Seitenleiste sollte anschließend **„Supabase-Datenbank verbunden“** stehen.

## Dateien für GitHub
- `app.py`
- `requirements.txt`
- `README.md`

`supabase_setup.sql` musst du nicht zwingend in GitHub hochladen; du brauchst die Datei nur einmal zum Einrichten der Datenbank.

## Hinweis zur Synchronisierung mit ChatGPT
Die Supabase-Datenbank macht die Daten innerhalb deiner Trading-App dauerhaft. Sie bedeutet **nicht automatisch**, dass ChatGPT in diesem Chat deine Änderungen sieht. Dafür wäre später eine explizite Verbindung/Integration zwischen ChatGPT und deiner Datenbank nötig.

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
