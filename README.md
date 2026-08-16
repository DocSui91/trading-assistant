# Trading Assistant V2.1

## Neu gegenüber V2
- Unternehmens-Kurzprofile für die Startwerte
- verständlichere News-Zusammenfassungen
- kombinierter Gesamt-Score
- separater Risiko-Score
- bessere Unterscheidung zwischen Hype und Einstiegsqualität
- Überhitzungswarnung über RSI
- verbesserter Hype Radar

## Secrets
In Streamlit Community Cloud:

```toml
TWELVE_DATA_API_KEY = "DEIN_TWELVE_DATA_KEY"
MARKETAUX_API_KEY = "DEIN_MARKETAUX_KEY"
```

## Deployment
`app.py`, `requirements.txt` und `README.md` im GitHub-Repository ersetzen. Streamlit aktualisiert anschließend die App.

## Noch offen
- automatische ISIN-Auflösung
- breiter Markt-Hype-Scanner außerhalb der Watchlist
- echte Fundamentaldaten
- automatische Turbo-/Knock-out-Produktauflösung
- Push-Mitteilungen
- Backtesting

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
