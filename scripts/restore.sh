#!/bin/bash
#
# FlowNavigator Database Restore Script
# Usage: ./restore.sh <backup_file.sql.gz>
#
# WARNING: This will DROP and recreate the database!
#

set -euo pipefail

# Configuration
BACKUP_FILE="${1:-}"
CONTAINER_NAME="${DB_CONTAINER:-flownavigator-db}"
DB_USER="${DB_USER:-flowaudit}"
DB_NAME="${DB_NAME:-flowaudit}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /home/janpow/Projekte/flownavigator/backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "=== FlowNavigator Database Restore ==="
echo "Backup file: ${BACKUP_FILE}"
echo "Target database: ${DB_NAME}"
echo ""
echo "WARNING: This will DROP and recreate the database!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container ${CONTAINER_NAME} is not running!"
    exit 1
fi

echo ""
echo "Stopping backend container..."
docker stop flownavigator-backend 2>/dev/null || true

echo "Dropping existing database..."
docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "Creating fresh database..."
docker exec "${CONTAINER_NAME}" psql -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "Restoring data..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Starting backend container..."
docker start flownavigator-backend 2>/dev/null || true

echo ""
echo "=== Restore completed successfully ==="
echo "Please verify the application is working correctly."
