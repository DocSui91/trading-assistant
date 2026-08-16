# Trading Assistant V2

Persönliche Streamlit-Web-App für Aktien und Knock-out/Turbos.

## Enthalten
- Twelve Data für Kurse
- Kurzfrist- und Mittelfrist-Score
- Marketaux News + Sentiment
- kombinierter Gesamt-Score
- Hype Radar auf Basis der beobachteten Werte
- Aktien hinzufügen/löschen
- Turbos hinzufügen/löschen
- Streamlit Secrets

## Streamlit Secrets
```toml
TWELVE_DATA_API_KEY = "DEIN_TWELVE_DATA_KEY"
MARKETAUX_API_KEY = "DEIN_MARKETAUX_KEY"
```

Die API-Keys niemals in GitHub eintragen.

## Nächste Ausbaustufen
- automatische ISIN-Auflösung
- breiter Hype-Markt-Scanner
- Fundamentaldaten/echte Unternehmensprofile
- KI-Zusammenfassungen
- Turbo-Produktdaten: Basiswert, Long/Short, Knock-out, Hebel
- Push-Mitteilungen
- Backtesting

Die Scores sind algorithmische Testsignale und keine Anlageberatung.
