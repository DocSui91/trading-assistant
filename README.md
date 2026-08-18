# Trading Assistant V2.6.2

## Korrektur: News werden strenger zugeordnet

Der von dir beobachtete Fehler – z. B. ein Infineon-Artikel unter Intel – soll mit V2.6.2 deutlich reduziert werden.

Die neue Logik:
- keine bloße Teilstring-Suche mehr
- exakte Wort-/Token-Grenzen
- deutsche RSS-News bevorzugen eindeutige Treffer im Titel
- Treffer nur im Beschreibungstext werden nur bei längeren Firmennamen akzeptiert
- Marketaux bevorzugt ein **exakt passendes Entity-Symbol**
- Fallback bei Marketaux nur über einen eindeutigen Firmennamen im Titel
- Neben-Erwähnungen und ähnlich geschriebene Unternehmen werden stärker herausgefiltert

## Weiterhin enthalten
- optionale Supabase-Datenbank
- Hype-Radar auf dem Dashboard
- deutsche RSS-News
- Marketaux-News
- englische Original-News
- optionale deutsche OpenAI-Auswertung
- Dienste-/Aboübersicht
- KI-Kostenbremse

## Update
Ersetze in GitHub:
- `app.py`
- `requirements.txt`
- `README.md`

`supabase_setup.sql` bleibt unverändert.
