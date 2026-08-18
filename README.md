# Trading Assistant V2.6.3

## News-Logik verbessert

V2.6.3 trennt klar zwischen:

### Allgemeine deutsche Börsen- und Aktien-News
Diese bleiben weiterhin sichtbar, auch wenn sie keiner deiner Aktien eindeutig zugeordnet werden.

### Aktienspezifische News
Ein Artikel wird nur unter einer Aktie angezeigt, wenn:
- die Überschrift eindeutig zum Unternehmen/Ticker passt
- der Inhalt nicht klar auf ein anderes Unternehmen fokussiert ist

Die Artikel erscheinen als Drop-down:
- außen siehst du die Originalüberschrift
- beim Öffnen siehst du die Zusammenfassung
- Überschrift und Inhalt werden vor der Zuordnung auf Konsistenz geprüft

### Turbo-News
Auch bei Turbos muss der hinterlegte Basiswert eindeutig in der Überschrift vorkommen.

## Update
Ersetze in GitHub:
- `app.py`
- `requirements.txt`
- `README.md`

`supabase_setup.sql` bleibt unverändert.
