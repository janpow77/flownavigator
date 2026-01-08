#!/bin/bash
# Startup Verification Script für flownavigator
# Prüft ob alle Container korrekt hochgefahren sind
# Usage: ./startup-check.sh

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
PROJECT_DIR="/home/janpow/Projekte/flownavigator"
MAX_WAIT=180  # 3 Minuten max wait time
CHECK_INTERVAL=5

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Container läuft?
check_container_running() {
    local container=$1
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        return 0
    else
        return 1
    fi
}

# Container ist healthy?
check_container_healthy() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")

    if [ "$status" = "healthy" ]; then
        return 0
    elif [ "$status" = "none" ]; then
        # Kein Health-Check definiert - prüfe nur ob läuft
        if check_container_running "$container"; then
            return 0
        fi
    fi
    return 1
}

# Warte auf Container
wait_for_container() {
    local container=$1
    local max_wait=$2
    local waited=0

    log_info "Warte auf Container: $container"

    while [ $waited -lt $max_wait ]; do
        if check_container_running "$container"; then
            log_success "Container $container läuft"
            return 0
        fi
        sleep $CHECK_INTERVAL
        waited=$((waited + CHECK_INTERVAL))
        echo -n "."
    done

    echo ""
    log_error "Container $container startet nicht (Timeout nach ${max_wait}s)"
    return 1
}

# Warte auf Health-Check
wait_for_healthy() {
    local container=$1
    local max_wait=$2
    local waited=0

    log_info "Warte auf Health-Check: $container"

    while [ $waited -lt $max_wait ]; do
        if check_container_healthy "$container"; then
            log_success "Container $container ist healthy"
            return 0
        fi

        # Status anzeigen
        local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        if [ "$status" != "none" ]; then
            echo -n "[$status]"
        fi

        sleep $CHECK_INTERVAL
        waited=$((waited + CHECK_INTERVAL))
        echo -n "."
    done

    echo ""
    log_warning "Container $container nicht healthy (Timeout nach ${max_wait}s)"
    return 1
}

# HTTP Endpoint prüfen
check_http_endpoint() {
    local url=$1
    local expected=$2
    local max_wait=$3
    local waited=0

    log_info "Prüfe HTTP Endpoint: $url"

    while [ $waited -lt $max_wait ]; do
        if timeout 5 curl -sf "$url" | grep -q "$expected" 2>/dev/null; then
            log_success "Endpoint $url antwortet korrekt"
            return 0
        fi
        sleep $CHECK_INTERVAL
        waited=$((waited + CHECK_INTERVAL))
        echo -n "."
    done

    echo ""
    log_error "Endpoint $url antwortet nicht (Timeout nach ${max_wait}s)"
    return 1
}

# Datenbank-Verbindung prüfen
check_database() {
    local container=$1
    local user=$2
    local database=$3

    log_info "Prüfe Datenbank-Verbindung..."

    if docker exec "$container" psql -U "$user" -d "$database" -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Datenbank-Verbindung OK"

        # Tabellen-Anzahl prüfen
        local table_count=$(docker exec "$container" psql -U "$user" -d "$database" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)
        log_info "Tabellen in Datenbank: $table_count"

        if [ "$table_count" -lt 1 ]; then
            log_warning "Nur $table_count Tabellen - Datenbank könnte leer sein!"
        fi

        return 0
    else
        log_error "Datenbank-Verbindung fehlgeschlagen"
        return 1
    fi
}

# Main Startup Check
main() {
    echo "=========================================="
    echo "  flownavigator Startup Verification"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo ""

    cd "$PROJECT_DIR" || exit 1

    # Schritt 1: Docker läuft?
    log_info "Prüfe Docker-Daemon..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker läuft nicht!"
        exit 1
    fi
    log_success "Docker läuft"
    echo ""

    # Schritt 2: Container starten (falls nicht laufen)
    log_info "Prüfe ob Container laufen..."

    # Zähle laufende flownavigator Container
    local running_count=$(docker ps --filter "name=flownavigator" --format "{{.Names}}" | wc -l)

    if [ $running_count -lt 3 ]; then
        log_info "Nur $running_count Container laufen - starte alle..."
        docker-compose up -d
    else
        log_success "Container laufen bereits ($running_count aktiv)"
    fi
    echo ""

    # Schritt 3: Datenbank
    log_info "=== Phase 1: Datenbank ==="

    wait_for_container "flownavigator-db" 30 || exit 1
    wait_for_healthy "flownavigator-db" 60 || log_warning "DB nicht healthy, fahre fort..."

    check_database "flownavigator-db" "flowaudit" "flowaudit" || exit 1
    echo ""

    # Schritt 4: Backend
    log_info "=== Phase 2: Backend ==="
    wait_for_container "flownavigator-backend" 30 || exit 1
    wait_for_healthy "flownavigator-backend" 120 || log_warning "Backend nicht healthy, prüfe trotzdem..."

    # Backend HTTP Check (falls Health-Endpoint existiert)
    check_http_endpoint "http://localhost:8001/api/health" "healthy" 60 || log_warning "Health-Check fehlgeschlagen, aber Backend könnte trotzdem laufen"
    echo ""

    # Schritt 5: Frontend
    log_info "=== Phase 3: Frontend ==="
    wait_for_container "flownavigator-frontend" 30 || exit 1

    # Frontend HTTP Check
    check_http_endpoint "http://localhost:3001" "html" 90 || log_error "Frontend antwortet nicht!"
    echo ""

    # Finale Zusammenfassung
    echo "=========================================="
    echo "  Startup Verification Abgeschlossen"
    echo "=========================================="
    echo ""

    # Status-Übersicht
    log_info "Container-Status:"
    docker ps --filter "name=flownavigator" --format "table {{.Names}}\t{{.Status}}" | grep -v "NAMES"

    echo ""
    log_info "Zugangspunkte:"
    echo "  Frontend: http://localhost:3001"
    echo "  Backend:  http://localhost:8001"
    echo "  DB:       localhost:5436"
    echo ""

    # Warnungen sammeln
    local warnings=0

    if ! check_container_healthy "flownavigator-db"; then
        warnings=$((warnings + 1))
    fi

    if ! check_container_healthy "flownavigator-backend"; then
        warnings=$((warnings + 1))
    fi

    if [ $warnings -gt 0 ]; then
        echo ""
        log_warning "$warnings Container sind nicht 'healthy' - prüfe Logs mit:"
        echo "  docker-compose logs -f"
        echo ""
        exit 1
    fi

    echo ""
    log_success "Alle kritischen Services laufen!"
    echo ""
}

# Hilfsfunktion für cron/systemd
if [ "$1" = "--quiet" ]; then
    main >/dev/null 2>&1
    exit $?
elif [ "$1" = "--help" ]; then
    echo "Usage: $0 [--quiet|--help]"
    echo ""
    echo "Optionen:"
    echo "  --quiet   Keine Ausgabe (nur Exit-Code)"
    echo "  --help    Diese Hilfe"
    echo ""
    echo "Exit-Codes:"
    echo "  0  Alle Services laufen"
    echo "  1  Fehler beim Startup"
    exit 0
else
    main
fi
