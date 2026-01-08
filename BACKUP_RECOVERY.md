# Backup & Recovery Guide - flownavigator

**Erstellt**: 2026-01-08
**Projekt**: FlowNavigator (flownavigator)

## Überblick

Dieser Guide beschreibt das Backup-System für flownavigator und die Wiederherstellung nach Datenverlust oder Stromausfällen.

## Automatische Backups

### Backup-Schedule

```bash
# Tägliches Backup um 02:00 Uhr
0 2 * * * /home/janpow/Projekte/flownavigator/scripts/backup.sh daily

# Wöchentliches Backup Sonntags um 03:00 Uhr
0 3 * * 0 /home/janpow/Projekte/flownavigator/scripts/backup.sh weekly
```

### Backup-Speicherorte

**Lokal**: `/home/janpow/Projekte/flownavigator/backups/`
- Tägliche Backups werden 7 Tage aufbewahrt
- Wöchentliche Backups werden 30 Tage aufbewahrt
- Manuelle Backups werden 90 Tage aufbewahrt

**Google Drive**: `gdrive:Backups/FlowNavigator`
- Synchronisation nach jedem Backup empfohlen
- Alle Backups sollten synchronisiert werden (ohne .log Dateien)

### Backup-Größen (Referenz)

```
~70-110 KB   = Aktuelle Backups (2026-01)
Größe variiert je nach Datenvolumen
```

## Manuelles Backup erstellen

```bash
# Sofortiges Backup
/home/janpow/Projekte/flownavigator/scripts/backup.sh manual

# Backup-Status anzeigen
ls -lht /home/janpow/Projekte/flownavigator/backups/*.sql.gz | head -5
```

### Google Drive Sync (manuell)

```bash
# Backups zu GDrive synchronisieren
rclone sync /home/janpow/Projekte/flownavigator/backups gdrive:Backups/FlowNavigator \
    --exclude "*.log" \
    --progress

# Backups auf GDrive anzeigen
rclone ls gdrive:Backups/FlowNavigator

# Backup von GDrive herunterladen
rclone copy gdrive:Backups/FlowNavigator/daily_flowaudit_YYYYMMDD_HHMMSS.sql.gz ~/Downloads/
```

## Backup-Verifizierung

### 1. Lokale Backups prüfen

```bash
# Liste der lokalen Backups
ls -lh /home/janpow/Projekte/flownavigator/backups/*.sql.gz

# Neuestes Backup prüfen
ls -lht /home/janpow/Projekte/flownavigator/backups/*.sql.gz | head -1
```

**WICHTIG**: Backups < 5 KB sind verdächtig! Normale Backups sind 70-110 KB oder größer.

### 2. Google Drive Backups prüfen

```bash
# Alle Backups auf GDrive auflisten
rclone ls gdrive:Backups/FlowNavigator

# Nur aktuelle Backups (letzte 25 Stunden)
rclone ls gdrive:Backups/FlowNavigator --max-age 25h
```

### 3. Automatische Backup-Prüfung

```bash
# Tägliche Backup-Prüfung (empfohlen)
/home/janpow/scripts/check-backups.sh
```

## Wiederherstellung nach Datenverlust

### Schritt 1: Situation analysieren

```bash
# Container-Status prüfen
docker ps --filter "name=flownavigator"

# Datenbank-Container läuft?
docker ps | grep flownavigator-db
```

### Schritt 2: Datenbank-Container sicherstellen

```bash
# Falls DB-Container nicht läuft
cd /home/janpow/Projekte/flownavigator
docker-compose up -d db

# Container-Namen notieren
docker ps --filter "name=flownavigator-db" --format "{{.Names}}"
```

### Schritt 3: Backup auswählen

**Option A: Lokales Backup (schneller)**
```bash
# Liste der lokalen Backups
ls -lht /home/janpow/Projekte/flownavigator/backups/*.sql.gz | head -5

# Neuestes verwenden oder spezifisches Datum wählen
BACKUP_FILE="/home/janpow/Projekte/flownavigator/backups/daily_flowaudit_YYYYMMDD_HHMMSS.sql.gz"
```

**Option B: Von Google Drive (falls lokal gelöscht)**
```bash
# Verfügbare Backups auf GDrive ansehen
rclone ls gdrive:Backups/FlowNavigator

# Backup herunterladen
mkdir -p /tmp/backup_restore
rclone copy "gdrive:Backups/FlowNavigator/daily_flowaudit_YYYYMMDD_HHMMSS.sql.gz" /tmp/backup_restore/

BACKUP_FILE="/tmp/backup_restore/daily_flowaudit_YYYYMMDD_HHMMSS.sql.gz"
```

### Schritt 4: Datenbank wiederherstellen

```bash
# WICHTIG: Container-Namen anpassen falls anders!
DB_CONTAINER="flownavigator-db"
DB_USER="flowaudit"
DB_NAME="flowaudit"

# Backup einspielen
echo "Wiederherstellung startet..."
zcat "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"

echo "Wiederherstellung abgeschlossen!"
```

### Schritt 5: Verifizierung

```bash
# Tabellen prüfen
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"

# Datenmenge prüfen (Beispiele)
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM users;" || echo "Tabelle users nicht vorhanden"
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM projects;" || echo "Tabelle projects nicht vorhanden"
```

**Erwartete Ausgabe**:
```
Mehrere Tabellen (Anzahl variiert)
Benutzer und Projekte je nach Nutzung
```

### Schritt 6: Backend neu starten

```bash
cd /home/janpow/Projekte/flownavigator

# Backend neu starten (führt ggf. Migrationen aus)
docker-compose restart backend

# Logs prüfen
docker-compose logs -f backend
```

**Erfolg**: Backend sollte ohne Fehler starten.

## Disaster Recovery - Komplett-Wiederherstellung

Falls **ALLES verloren** ist (Volumes gelöscht, Container weg):

### 1. Volumes löschen (falls korrupt)

```bash
cd /home/janpow/Projekte/flownavigator

# NUR wenn Volumes korrupt sind!
docker-compose down
docker volume rm flownavigator_postgres_data || true
docker volume rm pnpm_store || true
```

### 2. Container neu erstellen

```bash
# Alle Container neu starten
docker-compose up -d

# Warten bis DB bereit ist
sleep 10
docker logs flownavigator-db
```

### 3. Backup wiederherstellen

Siehe Schritt 3-6 oben.

### 4. Alle Container prüfen

```bash
docker ps --filter "name=flownavigator" --format "table {{.Names}}\t{{.Status}}"
```

**Alle sollten "healthy" oder "Up" sein**

## Härtung gegen Stromausfälle

### Automatische Container-Neustarts

In `docker-compose.yml` sollte für kritische Container eingestellt sein:
```yaml
restart: unless-stopped
```

**Bedeutung**: Container starten automatisch nach Systemstart neu.

### PostgreSQL Crash-Recovery

PostgreSQL hat integriertes Write-Ahead-Logging (WAL):
- Automatisches Recovery nach Stromausfall
- Keine Datenverlust bei ordnungsgemäßem Shutdown
- Crash-Recovery läuft automatisch beim Container-Start

### Nach Stromausfall

**Was passiert automatisch**:
1. Server startet neu
2. Docker-Daemon startet
3. Alle Container mit `restart: unless-stopped` starten automatisch
4. PostgreSQL führt Crash-Recovery durch (falls nötig)
5. Backend führt ggf. Migrationen aus
6. Anwendung ist wieder online

**Manuelle Prüfung empfohlen**:
```bash
# Container-Status
docker ps --filter "name=flownavigator"

# Datenbank-Logs auf Fehler prüfen
docker logs flownavigator-db | grep -i error

# Backend-Logs prüfen
docker logs flownavigator-backend --tail 50
```

## Backup-Monitoring

### Automatisches Monitoring einrichten

```bash
# Crontab bearbeiten
crontab -e

# Diese Zeile hinzufügen für tägliche Prüfung um 12:00 Uhr
0 12 * * * /home/janpow/scripts/check-backups.sh >> /home/janpow/logs/backup-check.log 2>&1
```

## Häufige Probleme

### Problem: Backend startet nicht

**Symptome**: Container läuft nicht oder crasht sofort

**Lösung**:
```bash
# Logs prüfen
docker-compose logs -f backend

# Container neu starten
docker-compose restart backend
```

### Problem: Frontend zeigt "Connection refused"

**Prüfung**:
```bash
# Frontend erreichbar?
curl http://localhost:3001
```

Falls HTML zurückkommt: Frontend funktioniert!

### Problem: Backup ist leer (< 1 KB)

**Ursache**: Datenbank-Container lief nicht während Backup

**Lösung**:
```bash
# Container-Status prüfen
docker ps | grep flownavigator-db

# Manuelles Backup erstellen
/home/janpow/Projekte/flownavigator/scripts/backup.sh manual

# Größe prüfen
ls -lh /home/janpow/Projekte/flownavigator/backups/*.sql.gz | tail -1
```

### Problem: GDrive-Sync schlägt fehl

**Symptome**:
```
ERROR: Google Drive nicht erreichbar
```

**Lösung**:
```bash
# rclone-Mount prüfen
mount | grep gdrive

# Falls nicht gemountet - Service neu starten
sudo systemctl restart rclone-mount

# rclone neu authentifizieren (falls Token abgelaufen)
rclone config reconnect gdrive:
```

## Backup-Log-Analyse

### Backup-Log ansehen

```bash
# Letzten 100 Zeilen
tail -100 /home/janpow/Projekte/flownavigator/backups/backup.log

# Nur Fehler/Warnungen
grep -E "(ERROR|FEHLER|WARNING)" /home/janpow/Projekte/flownavigator/backups/backup.log

# Heutiges Backup
grep "$(date +%Y-%m-%d)" /home/janpow/Projekte/flownavigator/backups/backup.log
```

### Erfolgreiche Backup-Meldungen

```
=== FlowNavigator Database Backup ===
Type: daily
Backup completed: XXK
=== Backup completed successfully ===
```

## Sicherheit

### Backup-Verschlüsselung

Die Backups sind **komprimiert aber NICHT verschlüsselt**!

Falls Verschlüsselung nötig:

```bash
# Manuell verschlüsseln
gpg --encrypt --recipient deine@email.com backup.sql.gz

# Entschlüsseln
gpg --decrypt backup.sql.gz.gpg > backup.sql.gz
```

### Zugriffskontrolle

```bash
# Backup-Verzeichnis-Berechtigungen prüfen
ls -ld /home/janpow/Projekte/flownavigator/backups/

# Sollte sein: drwxr-x--- oder ähnlich (nicht world-readable)
```

## Notfall-Kontakte

**Bei Problemen**:
1. Logs prüfen (siehe oben)
2. DOCKER_OPERATIONS.md lesen: `/home/janpow/Projekte/DOCKER_OPERATIONS.md`
3. Backup-Skript prüfen: `/home/janpow/Projekte/flownavigator/scripts/backup.sh`

## Checkliste - Regelmäßige Wartung

**Wöchentlich**:
- [ ] Backup-Status prüfen: `/home/janpow/scripts/check-backups.sh`
- [ ] GDrive-Backups verifizieren: `rclone ls gdrive:Backups/FlowNavigator`

**Monatlich**:
- [ ] Wiederherstellung testen (aus Backup wiederherstellen in Test-Umgebung)
- [ ] Alte Backups auf GDrive aufräumen (>30 Tage)

**Nach jedem Stromausfall**:
- [ ] Container-Status prüfen
- [ ] Datenbank-Logs auf Fehler prüfen
- [ ] Manuelles Backup erstellen
- [ ] Frontend/Backend Funktionstest

---

**Lessons Learned**:
- Backups sind essentiell
- NIEMALS `docker-compose down -v` verwenden (löscht Volumes!)
- Lokale Backups sind schneller als GDrive-Downloads
- Regelmäßige Verifikation ist wichtig

**Erstellt von**: Claude Sonnet 4.5
**Datum**: 2026-01-08
