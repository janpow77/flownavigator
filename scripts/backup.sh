#!/bin/bash
#
# FlowNavigator Database Backup Script
# Usage: ./backup.sh [daily|weekly|manual|sync|status]
#
# Cron entries (add with: crontab -e):
# Daily backup at 02:00:   0 2 * * * /home/janpow/Projekte/flownavigator/scripts/backup.sh daily
# Weekly backup Sunday:    0 3 * * 0 /home/janpow/Projekte/flownavigator/scripts/backup.sh weekly
# Sync to Google Drive:    0 4 * * * /home/janpow/Projekte/flownavigator/scripts/backup.sh sync
#

set -euo pipefail

# Configuration
BACKUP_TYPE="${1:-manual}"
PROJECT_DIR="/home/janpow/Projekte/flownavigator"
BACKUP_DIR="${PROJECT_DIR}/backups"
CONTAINER_NAME="flownavigator-db"
DB_USER="flowaudit"
DB_NAME="flowaudit"
GDRIVE_REMOTE="gdrive:Backups/FlowNavigator"

# Retention
RETENTION_DAYS_DAILY=7
RETENTION_DAYS_WEEKLY=30
RETENTION_DAYS_MANUAL=90

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${BACKUP_DIR}/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Sync to Google Drive
sync_to_gdrive() {
    log "=== Syncing to Google Drive ==="

    if ! command -v rclone &> /dev/null; then
        log "ERROR: rclone not installed"
        return 1
    fi

    # Sync all backups to Google Drive
    rclone sync "${BACKUP_DIR}" "${GDRIVE_REMOTE}" \
        --exclude "*.log" \
        --progress \
        2>&1 | tee -a "${LOG_FILE}"

    log "Sync completed"

    # Show Google Drive contents
    log "Google Drive contents:"
    rclone ls "${GDRIVE_REMOTE}" 2>&1 | tee -a "${LOG_FILE}"
}

# Database backup
backup_database() {
    local BACKUP_FILE="${BACKUP_DIR}/${BACKUP_TYPE}_${DB_NAME}_${TIMESTAMP}.sql.gz"

    log "=== FlowNavigator Database Backup ==="
    log "Type: ${BACKUP_TYPE}"
    log "Target: ${BACKUP_FILE}"

    # Check container
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log "ERROR: Container ${CONTAINER_NAME} not running!"
        return 1
    fi

    # Perform backup
    log "Starting backup..."
    docker exec "${CONTAINER_NAME}" pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=plain \
        --no-owner \
        --no-privileges \
        | gzip > "${BACKUP_FILE}"

    # Verify
    if [ ! -s "${BACKUP_FILE}" ]; then
        log "ERROR: Backup file is empty!"
        rm -f "${BACKUP_FILE}"
        return 1
    fi

    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    log "Backup completed: ${BACKUP_SIZE}"

    # Cleanup old backups
    case "${BACKUP_TYPE}" in
        daily)  RETENTION_DAYS=${RETENTION_DAYS_DAILY} ;;
        weekly) RETENTION_DAYS=${RETENTION_DAYS_WEEKLY} ;;
        *)      RETENTION_DAYS=${RETENTION_DAYS_MANUAL} ;;
    esac

    log "Cleaning backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -name "${BACKUP_TYPE}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

    # List backups
    log "Current backups:"
    ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || log "No backups found"
}

# Main
case "${BACKUP_TYPE}" in
    sync)
        sync_to_gdrive
        ;;
    daily|weekly|manual)
        backup_database
        # Auto-sync after backup
        sync_to_gdrive
        ;;
    status)
        log "=== Backup Status ==="
        log "Local backups:"
        ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || log "No local backups"
        log ""
        log "Google Drive backups:"
        rclone ls "${GDRIVE_REMOTE}" 2>/dev/null || log "Cannot access Google Drive"
        ;;
    *)
        echo "Usage: $0 [daily|weekly|manual|sync|status]"
        exit 1
        ;;
esac

log "=== Done ==="
