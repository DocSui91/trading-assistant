# Trading Assistant V2.3

## Neu
- OpenAI-Integration für deutsche News-Aufbereitung
- deutsche Überschrift, Kurzfassung, Auswirkung, Relevanz, Zeithorizont und Einordnung
- KI nur für relevante Meldungen
- Artikel-Cache: dieselbe Meldung wird nicht erneut kostenpflichtig ausgewertet
- frei einstellbares Monatslimit in Euro
- Monatslimit kann jederzeit geändert werden, z. B. 3 € oder 5 €
- zusätzlich frei einstellbares Tageslimit für KI-Auswertungen
- Kostenanzeige und automatische Sperre bei Erreichen des App-Limits
- Push-Kandidaten ab hoher Relevanz

## Benötigte Streamlit Secrets

```toml
TWELVE_DATA_API_KEY = "..."
MARKETAUX_API_KEY = "..."
OPENAI_API_KEY = "..."
```

## Wichtig zur Kostenbremse
Das in der App eingestellte Monatslimit ist eine app-interne Kostenbremse auf Basis geschätzter Tokenkosten. Es ist kein Ersatz für ein hartes Budget/Limits im OpenAI-API-Konto.

## Deployment
`app.py`, `requirements.txt` und `README.md` im GitHub-Repository ersetzen.

Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.
