# Trading Assistant MVP

Ein kostenloser, modularer Prototyp für deine persönliche Aktien-/Turbo-Watchlist.

## Aktuell enthalten
- Aktien hinzufügen/löschen
- Depot vs. Watchlist
- vier Start-Turbos
- Twelve Data Kursabfragen
- Tageschart
- erster technischer Test-Score
- RSI, SMA20, SMA50, Momentum
- einfache Handlungskategorie

## Noch nicht enthalten
- News + KI-Zusammenfassung
- Push-Mitteilungen
- automatische ISIN-Auflösung für jedes Produkt
- Zertifikate-/Turbo-Produktdaten (Knock-out, Hebel, Bezugsverhältnis)
- echtes Backtesting
- Broker-Anbindung

## Lokal starten

1. Python 3.11+ installieren.
2. Terminal im Projektordner öffnen.
3. `pip install -r requirements.txt`
4. `streamlit run app.py`
5. Im Browser den Twelve-Data-Key links eingeben.

Alternativ als Umgebungsvariable:
`TWELVE_DATA_API_KEY=...`

Den API-Key niemals in GitHub oder in den Quellcode schreiben.

## Twelve Data
Die App nutzt zunächst die REST-Endpunkte `/quote` und `/time_series`.
Die kostenlose Nutzung ist für den persönlichen Test gedacht. Für eine öffentliche/client-facing Anwendung müssen die Lizenzbedingungen des Datenanbieters geprüft werden.

## Startwerte
Wacker Chemie, Robinhood Markets, NVIDIA, Intel, Siemens Energy, D-Wave Quantum sowie AMD und ASML als Watchlist. Die vier vom Nutzer genannten Turbos sind ebenfalls vorgemerkt.
