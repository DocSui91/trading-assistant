# Trading Assistant V2.3.1

## Neu gegenüber V2.3
- Original-News bleiben immer auf Englisch sichtbar
- Originaltitel und Originalbeschreibung werden unverändert angezeigt
- bei vorhandenem OpenAI-Key erscheint darunter zusätzlich die deutsche Übersetzung/Zusammenfassung
- ohne OpenAI-Key bleibt der Hinweis bestehen; die englischen Original-News können trotzdem genutzt werden
- ideal zum parallelen Englischlernen und zur schnellen deutschen Einordnung

## Weiterhin enthalten
- Twelve Data für Kurse
- Marketaux für News
- OpenAI für deutsche Aufbereitung
- frei einstellbares Monatslimit in Euro
- frei einstellbares Tageslimit für KI-Auswertungen
- Artikel-Cache
- Push-Kandidaten ab hoher Relevanz
- technische Kurz-/Mittelfristanalyse
- Hype Radar

## Streamlit Secrets

```toml
TWELVE_DATA_API_KEY = "..."
MARKETAUX_API_KEY = "..."
OPENAI_API_KEY = "..."   # optional; ohne diesen Key bleiben die englischen News sichtbar
```

## Deployment
`app.py`, `requirements.txt` und `README.md` im GitHub-Repository ersetzen.

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
