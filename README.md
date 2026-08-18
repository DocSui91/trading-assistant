# Trading Assistant V2.8

## Neu: Depotpositionen
Für Depotwerte kannst du jetzt hinterlegen:
- Stückzahl
- durchschnittlicher Einstandskurs

Daraus berechnet die App:
- investiertes Kapital
- aktuellen Positionswert
- Gewinn / Verlust
- Gewinn / Verlust in %

## Neu: Nachkauf-Score
Der Nachkauf-Score ist **getrennt vom normalen Marktsignal**.

Wichtig:
Ein niedriger Einstand oder ein Verlust im Depot führt **nicht automatisch** zu einem besseren Nachkauf-Score. Entscheidend bleiben:
- Markt-/Techniksignal
- Risiko
- News
- Überhitzung
- bestehende Positionslage

## Neu: Nachkauf-Simulator
Du kannst eingeben:
- zusätzliche Stückzahl
- geplanter Kaufkurs

Die App zeigt:
- neuen durchschnittlichen Einstand
- neue Gesamtstückzahl
- zusätzlich benötigtes Kapital
- gesamtes investiertes Kapital

Der Simulator verändert deine echten Depotdaten nicht.

## Signal-Historie
V2.7-Funktionen bleiben vollständig erhalten:
- Signal speichern
- nach 5/10/20 Handelstagen beobachten
- Trefferquote
- durchschnittliche Performance

## Supabase
Wenn du Supabase nutzt, führe die neue `supabase_setup.sql` einmal aus.
Sie ergänzt:
- `quantity`
- `avg_entry`

für `assets` und `signals`.

## Update
Ersetze in GitHub:
- `app.py`
- `requirements.txt`
- `README.md`

Wenn du Supabase verwendest:
- `supabase_setup.sql` einmal im SQL Editor ausführen.

Danach ist ein guter Zeitpunkt für die 2–4-wöchige Testphase.
