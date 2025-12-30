#!/bin/bash
#
# FlowNavigator Database Backup Script
# Usage: ./backup.sh [daily|weekly|manual]
#
# Recommended cron entries:
# Daily backup at 2:00 AM:   0 2 * * * /path/to/backup.sh daily
# Weekly backup on Sunday:   0 3 * * 0 /path/to/backup.sh weekly
#

set -euo pipefail

# Configuration
BACKUP_TYPE="${1:-manual}"
BACKUP_DIR="${BACKUP_DIR:-/home/janpow/Projekte/flownavigator/backups}"
CONTAINER_NAME="${DB_CONTAINER:-flownavigator-db}"
DB_USER="${DB_USER:-flowaudit}"
DB_NAME="${DB_NAME:-flowaudit}"
RETENTION_DAYS_DAILY=7
RETENTION_DAYS_WEEKLY=30
RETENTION_DAYS_MANUAL=90

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Generate timestamp and filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_TYPE}_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "=== FlowNavigator Database Backup ==="
echo "Type: ${BACKUP_TYPE}"
echo "Timestamp: ${TIMESTAMP}"
echo "Target: ${BACKUP_FILE}"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container ${CONTAINER_NAME} is not running!"
    exit 1
fi

# Perform backup
echo "Starting backup..."
docker exec "${CONTAINER_NAME}" pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Verify backup
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file is empty!"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup completed: ${BACKUP_SIZE}"

# Cleanup old backups based on type
case "${BACKUP_TYPE}" in
    daily)
        RETENTION_DAYS=${RETENTION_DAYS_DAILY}
        ;;
    weekly)
        RETENTION_DAYS=${RETENTION_DAYS_WEEKLY}
        ;;
    manual)
        RETENTION_DAYS=${RETENTION_DAYS_MANUAL}
        ;;
    *)
        RETENTION_DAYS=${RETENTION_DAYS_MANUAL}
        ;;
esac

echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "${BACKUP_TYPE}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# List current backups
echo ""
echo "Current backups:"
ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || echo "No backups found"

echo ""
echo "=== Backup completed successfully ==="
