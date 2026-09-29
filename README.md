# Trading Assistant V2.9.3

## Kursdaten stabilisiert
- Twelve-Data-Kursabfragen werden 60 Sekunden gecacht, damit derselbe Wert nicht mehrfach unnötig abgefragt wird.
- Tageskursdaten werden 5 Minuten gecacht.
- Wenn der Live-Quote fehlschlägt, versucht die App automatisch den letzten Tages-Schlusskurs.
- API-Fehler werden unter „Kursdaten-Diagnose“ sichtbar statt still als „—“ dargestellt.

## Meine Werte
- Keine intern scrollbar dargestellte Dataframe-Tabelle mehr.
- Die Tabelle wird vollständig in die Seite eingebettet und scrollt mit der gesamten Seite.

## Depot-Eingaben
- Stückzahl und Ø Einstandskurs werden beim Hinzufügen nur angezeigt, wenn „Depot“ gewählt ist.
- Beim Bearbeiten gilt dasselbe.

## Supabase
Die Supabase-Persistenz und der Systemcheck aus V2.9.2 bleiben erhalten.

## Version 2.9.4
- Maximal 8 automatische Twelve-Data-Kursabrufe pro Lauf.
- Kurs-Cache für 15 Minuten; persistente Speicherung in Supabase (`market_cache`).
- Dashboard zeigt gespeicherte Kurse sofort und aktualisiert nur fällige Werte.
- Hype-Radar im Dashboard wird nur noch manuell berechnet, damit keine versteckten Kursreihen-Abfragen das Minutenlimit verbrauchen.
- `Meine Werte` bleibt eine normale, mit der Seite wachsende Tabelle ohne eigenen vertikalen Scrollbereich.

**Einmalig:** Den neuen Abschnitt aus `supabase_setup.sql` im Supabase SQL Editor ausführen, damit der Kurs-Cache auch über Neustarts hinweg erhalten bleibt.
