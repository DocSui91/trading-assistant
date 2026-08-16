# Trading Assistant V2.2

## Neu gegenüber V2.1
- eigener 📰 News-Reiter
- Filter: Alle / Depot / Watchlist
- Filter: Positiv / Neutral / Negativ
- Mindest-Relevanz 1–10
- Relevanzbewertung je Nachricht
- Stimmung je Nachricht
- Handlungseinschätzung je Nachricht
- Vorbereitung für spätere Push-Logik
- hohe Relevanz (>= 8/10) wird markiert

## Secrets
```toml
TWELVE_DATA_API_KEY = "DEIN_TWELVE_DATA_KEY"
MARKETAUX_API_KEY = "DEIN_MARKETAUX_KEY"
```

## Deployment
`app.py`, `requirements.txt` und `README.md` im GitHub-Repository ersetzen.

## Noch offen
- automatische ISIN-Auflösung
- breiter Markt-News-/Hype-Scanner außerhalb der Watchlist
- echte Fundamentaldaten
- Turbo-/Knock-out-Produktauflösung
- echte Push-Mitteilungen
- Backtesting

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
