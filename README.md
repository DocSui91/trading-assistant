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
