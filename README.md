# Trading Assistant V2.4

## Neu gegenüber V2.3.1
- Bereich **Meine App-Dienste & Abos** direkt unter dem Dashboard
- eigener Reiter **Dienste & Abos**
- Status je Anbieter: kostenlos, kostenpflichtig, gekündigt, pausiert, nicht eingerichtet
- frei eintragbare Monatskosten
- frei eintragbares Verlängerungsdatum
- Notizfeld
- direkte Links zur offiziellen Verwaltung/Kündigung
- direkte Links zu Tarifen/Reaktivierung
- automatische Summe der von dir erfassten externen Monatskosten
- kostenlose deutschsprachige Recherchelinks:
  - finanzen.net
  - boerse.de
  - Tagesschau Finanzen

## Wichtig
Die App kündigt oder reaktiviert externe Dienste nicht selbst. Sie führt dich zur offiziellen Anbieter-Seite, wo du den Vorgang bestätigst.

## Weiterhin enthalten
- Twelve Data Kursdaten
- Marketaux News
- englische Original-News
- optionale deutsche OpenAI-Zusammenfassung
- frei einstellbare KI-Kostenbremse
- Hype Radar
- Aktien-/Turbo-Watchlist

## Streamlit Secrets
```toml
TWELVE_DATA_API_KEY = "..."
MARKETAUX_API_KEY = "..."
OPENAI_API_KEY = "..."   # optional
```

## Deployment
`app.py`, `requirements.txt` und `README.md` im GitHub-Repository ersetzen.

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
