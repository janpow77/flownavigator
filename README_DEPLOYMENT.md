# flownavigator - Deployment & Operations Guide

**Projekt**: FlowNavigator (flownavigator)
**Erstellt**: 2026-01-08
**Status**: Production Ready

## Schnellstart

```bash
cd /home/janpow/Projekte/flownavigator

# Container starten
docker-compose up -d

# Status prüfen (empfohlen nach jedem Start!)
./scripts/startup-check.sh
```

**Zugangspunkte nach erfolgreichem Start:**
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- Datenbank: localhost:5436

## Dokumentation

### Haupt-Dokumentation
- **BACKUP_RECOVERY.md** - Backup-System und Wiederherstellung nach Datenverlust
- **README_DEPLOYMENT.md** - Diese Datei (Deployment & Tägliche Operations)
- **/home/janpow/Projekte/DOCKER_OPERATIONS.md** - Allgemeine Docker Best Practices

### Skripte
- `scripts/backup.sh` - Backup-Skript (täglich um 02:00 Uhr empfohlen)
- `scripts/startup-check.sh` - Startup-Verifikation (prüft ob alle Container korrekt laufen)
- `scripts/restore.sh` - Wiederherstellungs-Skript
- `/home/janpow/scripts/check-backups.sh` - Backup-Monitoring (alle Projekte)

## Tägliche Operations

### Container starten

```bash
cd /home/janpow/Projekte/flownavigator

# Normale Methode
docker-compose up -d

# Mit Startup-Verifikation (empfohlen)
./scripts/startup-check.sh
```

### Container stoppen

```bash
cd /home/janpow/Projekte/flownavigator

# Alle Container stoppen
docker-compose stop

# NIEMALS VERWENDEN (löscht Daten!!!):
# docker-compose down -v
```

### Container neu starten

```bash
cd /home/janpow/Projekte/flownavigator

# Alle Container
docker-compose restart

# Einzelner Service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart db
```

### Status prüfen

```bash
# Container-Status
docker ps --filter "name=flownavigator" --format "table {{.Names}}\t{{.Status}}"

# Logs anzeigen
docker-compose logs -f

# Logs eines bestimmten Services
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Neueste 50 Zeilen
docker logs flownavigator-backend --tail 50
```

### Code-Änderungen deployen

```bash
cd /home/janpow/Projekte/flownavigator

# Backend (mit Hot-Reload)
docker-compose restart backend

# Frontend (mit Hot Module Replacement)
# Keine Aktion nötig - Vite macht HMR automatisch

# Bei größeren Änderungen: Neu bauen
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Backup-System

### Automatische Backups

**Empfohlener Cron-Schedule**:

```bash
# Tägliches Backup um 02:00 Uhr
0 2 * * * /home/janpow/Projekte/flownavigator/scripts/backup.sh daily

# Wöchentliches Backup Sonntags um 03:00 Uhr
0 3 * * 0 /home/janpow/Projekte/flownavigator/scripts/backup.sh weekly
```

**Speicherorte:**
- Lokal: `/home/janpow/Projekte/flownavigator/backups/`
- Cloud: `gdrive:Backups/FlowNavigator` (nach manuellem Sync)

### Manuelles Backup

```bash
# Sofort-Backup
/home/janpow/Projekte/flownavigator/scripts/backup.sh manual

# Backup-Monitoring (alle Projekte)
/home/janpow/scripts/check-backups.sh

# Status der Backups
ls -lht /home/janpow/Projekte/flownavigator/backups/*.sql.gz | head -5
```

### Backup-Wiederherstellung

**Siehe BACKUP_RECOVERY.md** für detaillierte Anleitung!

**Schnellreferenz:**
```bash
# 1. Backup-Datei wählen
BACKUP_FILE="/home/janpow/Projekte/flownavigator/backups/daily_flowaudit_YYYYMMDD_HHMMSS.sql.gz"

# 2. Wiederherstellen
zcat "$BACKUP_FILE" | docker exec -i flownavigator-db psql -U flowaudit -d flowaudit

# 3. Backend neu starten
docker-compose restart backend
```

## Problembehandlung

### Problem: Backend startet nicht

**Symptome**: Container crasht oder läuft nicht

**Lösung:**
```bash
# Logs prüfen
docker-compose logs -f backend

# Container neu starten
docker-compose restart backend

# Bei persistenten Problemen: Neu bauen
docker-compose up -d --build backend
```

### Problem: Frontend zeigt Fehler

**Symptome**: Seite lädt nicht oder zeigt Fehler

**Testen ob Frontend funktioniert**:
```bash
curl http://localhost:3001
```

Falls HTML zurückkommt: Frontend funktioniert!

**Lösung:**
```bash
# Logs prüfen
docker-compose logs -f frontend

# Container neu starten
docker-compose restart frontend
```

### Problem: Datenbank-Verbindung fehlgeschlagen

**Symptome**: Backend kann nicht zur DB verbinden

**Lösung**:
```bash
# DB-Container läuft?
docker ps | grep flownavigator-db

# DB-Container starten
docker-compose up -d db

# Health-Check prüfen
docker exec flownavigator-db pg_isready -U flowaudit -d flowaudit

# Logs prüfen
docker logs flownavigator-db
```

### Problem: Container startet nicht nach Stromausfall

```bash
# 1. Docker läuft?
systemctl status docker

# 2. Container manuell starten
cd /home/janpow/Projekte/flownavigator
docker-compose up -d

# 3. Mit Verifikation
./scripts/startup-check.sh
```

### Problem: Datenbank ist leer

```bash
# 1. Backup wiederherstellen (siehe BACKUP_RECOVERY.md)

# 2. Neuestes Backup verwenden
BACKUP_FILE=$(ls -t /home/janpow/Projekte/flownavigator/backups/*.sql.gz | head -1)
echo "Verwende: $BACKUP_FILE"

# 3. Wiederherstellen
zcat "$BACKUP_FILE" | docker exec -i flownavigator-db psql -U flowaudit -d flowaudit

# 4. Backend neu starten
docker-compose restart backend
```

### Problem: Port-Konflikt

**Symptome**: Container kann nicht starten wegen belegtem Port

**Lösung**:
```bash
# Welche Ports sind belegt?
ss -tlnp | grep -E ":(3001|8001|5436)"

# Port in docker-compose.yml anpassen oder anderen Container stoppen
```

## Sicherheit

### Wichtige Regeln

- **NIEMALS** `docker-compose down -v` verwenden (löscht Datenbanken!)
- **IMMER** Backup vor größeren Änderungen
- **NIEMALS** .env Datei committen
- **NIEMALS** Secrets in Logs ausgeben

### Zugriffskontrolle

```bash
# .env Datei Berechtigungen (falls vorhanden)
chmod 600 /home/janpow/Projekte/flownavigator/.env

# Backup-Verzeichnis
chmod 750 /home/janpow/Projekte/flownavigator/backups/

# Keine world-readable Dateien!
find /home/janpow/Projekte/flownavigator -type f -perm -004
```

## Monitoring

### Health-Checks

```bash
# Startup-Verifikation (empfohlen täglich)
/home/janpow/Projekte/flownavigator/scripts/startup-check.sh

# Backup-Status
/home/janpow/scripts/check-backups.sh

# Container-Status
docker ps --filter "name=flownavigator"

# Backend Health (falls implementiert)
curl http://localhost:8001/api/health | python3 -m json.tool
```

### Logs überwachen

```bash
# Live-Logs (alle Services)
docker-compose logs -f

# Nur Fehler
docker-compose logs | grep -i error

# Backend Fehler
docker logs flownavigator-backend 2>&1 | grep -E "(ERROR|FATAL|Exception)"
```

### Ressourcen-Nutzung

```bash
# CPU/RAM pro Container
docker stats --no-stream --filter "name=flownavigator"

# Disk-Nutzung
docker system df

# Volume-Größen
docker volume ls | grep flownavigator
docker system df -v | grep flownavigator
```

## Updates & Wartung

### Code-Updates (Git)

```bash
cd /home/janpow/Projekte/flownavigator

# 1. Backup erstellen (Sicherheit!)
./scripts/backup.sh manual

# 2. Code pullen
git pull origin main

# 3. Dependencies aktualisieren (falls nötig)
docker-compose build backend
docker-compose build frontend

# 4. Container neu starten
docker-compose up -d

# 5. Verifikation
./scripts/startup-check.sh
```

### Docker-Images aktualisieren

```bash
cd /home/janpow/Projekte/flownavigator

# Images aktualisieren
docker-compose pull

# Mit neuen Images starten
docker-compose up -d

# Alte Images aufräumen
docker image prune -f
```

## Disaster Recovery

### Nach Datenverlust

**Siehe BACKUP_RECOVERY.md** für vollständige Anleitung!

**Kurzfassung:**
1. Container starten: `docker-compose up -d`
2. Backup wählen: `ls -lht /home/janpow/Projekte/flownavigator/backups/`
3. Wiederherstellen: `zcat BACKUP | docker exec -i flownavigator-db psql ...`
4. Backend neu starten: `docker-compose restart backend`
5. Verifikation: `./scripts/startup-check.sh`

### Nach Stromausfall

1. System hochfahren (Docker startet automatisch)
2. Container starten automatisch durch `restart: unless-stopped` (falls konfiguriert)
3. **Empfohlen**: Manuelle Prüfung ausführen

```bash
# Status prüfen
./scripts/startup-check.sh

# Backup erstellen (nach Stromausfall immer!)
./scripts/backup.sh manual

# Logs auf Fehler prüfen
docker logs flownavigator-db | grep -i error
docker logs flownavigator-backend | grep -i error
```

## Performance

### Typische Ressourcen-Nutzung

```
Backend:  50-200 MB RAM, 1-5% CPU (idle)
Frontend: 50-100 MB RAM, <1% CPU
DB:       50-200 MB RAM, 1-10% CPU
```

### Performance-Probleme

**Backend langsam?**
- Prüfe Logs: `docker logs flownavigator-backend | tail -50`
- Neustart: `docker-compose restart backend`

**Datenbank langsam?**
- Prüfe Verbindungen: `docker exec flownavigator-db psql -U flowaudit -d flowaudit -c "SELECT COUNT(*) FROM pg_stat_activity;"`
- Vacuum empfohlen: `docker exec flownavigator-db psql -U flowaudit -d flowaudit -c "VACUUM ANALYZE;"`

## Netzwerk & Ports

### Port-Übersicht

| Service | Port (extern) | Port (intern) |
|---------|---------------|---------------|
| Frontend | 3001 | 5173 |
| Backend | 8001 | 8000 |
| PostgreSQL | 5436 | 5432 |

### Port-Konflikte prüfen

```bash
# Welche Ports sind belegt?
ss -tlnp | grep -E ":(3001|8001|5436)"

# Alle Docker-Container Ports
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

## Checkliste

### Tägliche Checks (automatisiert empfohlen)
- [ ] Backup läuft um 02:00 Uhr (cron)
- [ ] Backup-Status prüfen: `/home/janpow/scripts/check-backups.sh`

### Wöchentliche Checks
- [ ] Startup-Verifikation: `./scripts/startup-check.sh`
- [ ] Container-Logs auf Fehler prüfen
- [ ] Disk-Space prüfen: `df -h`
- [ ] Alte Logs aufräumen (optional)

### Monatliche Checks
- [ ] Backup-Wiederherstellung testen
- [ ] GDrive-Backups aufräumen (>30 Tage alt)
- [ ] Docker-Images aufräumen: `docker image prune -a`
- [ ] Performance-Check: `docker stats`

### Nach jedem Code-Update
- [ ] Backup erstellen
- [ ] Code pullen
- [ ] Container neu bauen (falls nötig)
- [ ] Startup-Verifikation

### Nach jedem Stromausfall
- [ ] Container-Status prüfen
- [ ] Logs auf Fehler prüfen
- [ ] Manuelles Backup erstellen
- [ ] Funktionstest (Frontend/Backend erreichbar?)

## Support

### Logs-Sammlung für Support

```bash
# Alle wichtigen Logs sammeln
mkdir -p ~/flownavigator_logs_$(date +%Y%m%d)
cd ~/flownavigator_logs_$(date +%Y%m%d)

# Container-Status
docker ps --filter "name=flownavigator" > container_status.txt

# Logs
docker logs flownavigator-backend --tail 200 > backend.log 2>&1
docker logs flownavigator-frontend --tail 200 > frontend.log 2>&1
docker logs flownavigator-db --tail 200 > db.log 2>&1

# docker-compose config
cd /home/janpow/Projekte/flownavigator
docker-compose config > ~/flownavigator_logs_$(date +%Y%m%d)/docker-compose-resolved.yml

# Startup-Check
./scripts/startup-check.sh > ~/flownavigator_logs_$(date +%Y%m%d)/startup-check.log 2>&1

# Komprimieren
cd ~
tar -czf flownavigator_logs_$(date +%Y%m%d).tar.gz flownavigator_logs_$(date +%Y%m%d)/
```

## Best Practices

1. **IMMER** Backup vor Änderungen
2. **NIEMALS** `docker-compose down -v` verwenden
3. **IMMER** `./scripts/startup-check.sh` nach Start ausführen
4. **NIEMALS** direkt in Produktion deployen (teste lokal!)
5. **IMMER** Logs prüfen nach Deployment
6. **NIEMALS** Secrets committen
7. **IMMER** `.env` Datei sichern (aber nicht ins Git!)

---

**Erstellt**: 2026-01-08
**Version**: 1.0
**Maintainer**: Jan
**Basis**: audit_designer Template
