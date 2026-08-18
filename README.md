# Trading Assistant V2.9

## Neu: ISIN-Autovervollständigung
Bei der Eingabe einer ISIN versucht die App über Twelve Data `/symbol_search` automatisch zu ergänzen:
- Name
- Ticker
- Börse
- Währung / Instrumenttyp als Rückmeldung

**Wichtig:** Twelve Data verlangt für ISIN-Suchen die Aktivierung des ISIN Data Add-ons. Falls dein Tarif/Zugang das nicht erlaubt, bleibt die manuelle Eingabe weiterhin möglich.

## Neu: Formular wird nach Hinzufügen geleert
Nach erfolgreichem Hinzufügen einer Aktie werden alle Eingabefelder zurückgesetzt:
- ISIN
- Name
- Ticker
- Börse
- Kategorie
- Stückzahl
- Einstandskurs

## Neu: Bestehende Aktien vollständig bearbeiten
Jede vorhandene Aktie hat jetzt einen aufklappbaren Bearbeitungsbereich. Dort kannst du korrigieren:
- Name
- ISIN
- Ticker
- Börse
- Depot / Watchlist
- Stückzahl
- durchschnittlicher Einstandskurs

Damit kannst du z. B. eine bereits beobachtete Aktie später ins Depot verschieben und Stückzahl/Kaufpreis ergänzen.

## Duplikatschutz
Wenn ISIN oder Ticker bereits vorhanden sind, wird die Aktie nicht doppelt hinzugefügt. Stattdessen weist die App darauf hin, den bestehenden Eintrag zu bearbeiten.

## Supabase
Die Speicherung von `quantity` und `avg_entry` wurde auch in der Supabase-Lade-/Speicherlogik korrigiert.

## Update
Ersetze in GitHub:
- `app.py`
- `requirements.txt`
- `README.md`

Wenn du Supabase nutzt, kannst du die mitgelieferte `supabase_setup.sql` erneut ausführen; die `ALTER TABLE ... IF NOT EXISTS`-Befehle sind wiederholbar.
