# Trading Assistant V2.9.1

## Fehlerbehebung
Beim Hinzufügen bzw. erneuten Erkennen einer ISIN konnte V2.9 eine
`StreamlitAPIException` auslösen.

Ursache:
Streamlit erlaubt nicht, dass der Wert eines bereits erzeugten Widgets im selben
Render-Durchlauf nachträglich über `st.session_state` verändert wird.

## Korrektur
V2.9.1 arbeitet zweistufig:

1. ISIN-Erkennung wird nur vorgemerkt.
2. Im nächsten Render-Durchlauf werden Name, Ticker und Börse **vor** dem Erzeugen
   der Widgets gesetzt.

Dasselbe gilt für den Formular-Reset nach „Aktie hinzufügen“:
- Aktie wird gespeichert
- neuer Render-Durchlauf
- Eingabefelder werden sicher geleert

## Weiterhin enthalten
- automatische ISIN-Auflösung, soweit Twelve Data sie erlaubt
- manuelle Eingabe als Fallback
- Bearbeiten bestehender Aktien
- Wechsel Watchlist ↔ Depot
- Stückzahl / Einstandskurs korrigieren
- Nachkauf-Simulator
- Signal-Historie
- News / Hype Radar / Supabase

## Update
Für den Fix reicht technisch `app.py`.
Empfohlen:
- `app.py`
- `requirements.txt`
- `README.md`

`supabase_setup.sql` ist unverändert.
