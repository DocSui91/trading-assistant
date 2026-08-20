# Trading Assistant V2.9.2

## Neu: echter Supabase-Systemcheck
Die Anzeige „Speicherung: Supabase“ reichte bisher nicht aus, weil sie nur prüfte,
ob ein Supabase-Client erzeugt werden konnte.

V2.9.2 prüft jetzt:
- Supabase Client
- assets lesen
- assets schreiben/löschen
- turbos lesen
- turbos schreiben/löschen
- signals lesen
- signals schreiben/löschen

Wenn alles funktioniert, erscheint:
**Persistente Speicherung: AKTIV**

## Datenbankfehler werden nicht mehr verschluckt
Fehler beim Lesen oder Schreiben werden jetzt in der App angezeigt.

## Wichtige Korrektur
Eine leere, aber erreichbare Supabase-Tabelle wird nicht mehr automatisch als
„Datenbank nicht verfügbar“ interpretiert. Dadurch werden Starterdaten nicht
unnötig erneut geladen.

## So testen
1. Dateien aktualisieren.
2. App öffnen.
3. `🗄️ Supabase-Systemcheck` öffnen.
4. `Datenbank jetzt testen` drücken.
5. Nur wenn alle Punkte grün sind, weitere Depot-/Watchlistdaten pflegen.

`supabase_setup.sql` muss für diesen reinen Diagnose-Fix nicht erneut ausgeführt
werden, sofern die Tabellen bereits angelegt wurden.
