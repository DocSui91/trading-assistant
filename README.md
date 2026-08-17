# Trading Assistant V2.6.1

## Fehlerbehebung
V2.6 enthielt einen Startfehler:
`NameError: supabase_client is not defined`.

V2.6.1 definiert die Supabase-Funktionen nun korrekt **vor dem ersten Aufruf**.

## Verhalten
- **Ohne Supabase:** Die App startet normal und nutzt die bisherige Sitzungsspeicherung.
- **Mit Supabase:** Depot, Watchlist und Turbos werden dauerhaft gespeichert.
- Der Hype-Radar bleibt direkt oben auf dem Dashboard.
- Deutsche RSS-News und Marketaux-News bleiben enthalten.

## Streamlit Secrets für Supabase (optional)

```toml
SUPABASE_URL = "https://DEIN-PROJEKT.supabase.co"
SUPABASE_SECRET_KEY = "DEIN_SUPABASE_SECRET_KEY"
```

## Update
Für die Fehlerbehebung reicht es technisch, `app.py` zu ersetzen.
Empfohlen ist aber wieder der Austausch von:
- `app.py`
- `requirements.txt`
- `README.md`

Die `supabase_setup.sql` brauchst du nur, wenn du Supabase einrichtest.
