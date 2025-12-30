# FlowNavigator Deployment Guide

## Voraussetzungen

- Docker >= 24.0
- Docker Compose >= 2.0
- 2 GB RAM (mindestens)
- 10 GB Speicherplatz

## Umgebungsvariablen

Erstellen Sie eine `.env` Datei im Root-Verzeichnis:

```bash
cp apps/backend/.env.example .env
```

### Erforderliche Variablen

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `DATABASE_URL` | PostgreSQL Connection String | `postgresql+asyncpg://user:pass@db:5432/flowaudit` |
| `SECRET_KEY` | JWT Secret (min. 32 Zeichen) | `your-super-secret-key-change-this` |
| `DEBUG` | Debug-Modus (false in Produktion!) | `false` |
| `CORS_ORIGINS` | Erlaubte Origins | `["https://your-domain.com"]` |

### Secret Key generieren

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Development Setup

```bash
# Container starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down
```

## Production Deployment

### 1. Umgebungsvariablen setzen

```bash
# .env für Produktion
DATABASE_URL=postgresql+asyncpg://flowaudit:SECURE_PASSWORD@db:5432/flowaudit
SECRET_KEY=your-generated-secret-key-here
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
```

### 2. Docker Compose für Produktion

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Datenbank-Migrationen

```bash
docker exec flownavigator-backend alembic upgrade head
```

### 4. Health-Check

```bash
curl http://localhost:8001/api/health
# Erwartet: {"api":"healthy","database":"healthy"}
```

## Backup & Restore

### Automatisches Backup

```bash
# Crontab einrichten
crontab -e

# Tägliches Backup um 2:00 Uhr
0 2 * * * /path/to/flownavigator/scripts/backup.sh daily

# Wöchentliches Backup Sonntags um 3:00 Uhr
0 3 * * 0 /path/to/flownavigator/scripts/backup.sh weekly
```

### Manuelles Backup

```bash
./scripts/backup.sh manual
```

### Restore

```bash
./scripts/restore.sh backups/manual_flowaudit_20241230_120000.sql.gz
```

## Monitoring

### Logs

```bash
# Alle Logs
docker-compose logs -f

# Nur Backend
docker-compose logs -f backend

# Mit Zeitstempel
docker-compose logs -f --timestamps
```

### Health Checks

- Backend: `GET /health` und `GET /api/health`
- Frontend: `GET /health`
- Database: `pg_isready`

### Metriken (Optional)

Rate-Limiting Metriken sind über Logs verfügbar. Für erweiterte Metriken empfehlen wir Prometheus + Grafana.

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker-compose logs backend

# Container-Status
docker ps -a
```

### Datenbank-Verbindung fehlgeschlagen

```bash
# DB Container prüfen
docker exec flownavigator-db pg_isready -U flowaudit

# Verbindung testen
docker exec flownavigator-db psql -U flowaudit -d flowaudit -c "SELECT 1"
```

### Rate-Limiting Fehler (429)

Wenn Sie 429-Fehler erhalten, warten Sie oder erhöhen Sie die Limits in `app/core/rate_limit.py`.

## Updates

```bash
# Code aktualisieren
git pull

# Container neu bauen
docker-compose build

# Container neustarten
docker-compose up -d

# Migrationen ausführen
docker exec flownavigator-backend alembic upgrade head
```

## Sicherheitsempfehlungen

1. **Niemals** `DEBUG=true` in Produktion
2. **Immer** einen sicheren `SECRET_KEY` setzen
3. **CORS_ORIGINS** auf spezifische Domains einschränken
4. Regelmäßige Backups durchführen
5. Docker-Images regelmäßig aktualisieren
6. Cloudflare oder ähnlichen Proxy für DDoS-Schutz nutzen
