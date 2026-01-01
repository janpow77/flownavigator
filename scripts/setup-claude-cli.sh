#!/bin/bash
#
# Setup-Script für Claude Code CLI auf NUC
# Führt alle notwendigen Installationen durch
#

set -e  # Bei Fehler abbrechen

echo "=========================================="
echo "  FlowNavigator - Claude CLI Setup"
echo "=========================================="
echo ""

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funktion für Status-Meldungen
ok() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

# 1. Node.js prüfen
echo "1. Prüfe Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    ok "Node.js gefunden: $NODE_VERSION"
else
    fail "Node.js nicht gefunden. Bitte installieren: https://nodejs.org/"
fi

# 2. pnpm prüfen/installieren
echo ""
echo "2. Prüfe pnpm..."
if command -v pnpm &> /dev/null; then
    ok "pnpm gefunden: $(pnpm --version)"
else
    warn "pnpm nicht gefunden, installiere..."
    npm install -g pnpm
    ok "pnpm installiert"
fi

# 3. Claude Code CLI installieren
echo ""
echo "3. Installiere Claude Code CLI..."
if command -v claude &> /dev/null; then
    ok "Claude CLI bereits installiert: $(claude --version 2>/dev/null || echo 'Version unbekannt')"
else
    pnpm add -g @anthropic-ai/claude-code
    ok "Claude CLI installiert"
fi

# 4. Python-Dependencies für Parser
echo ""
echo "4. Installiere Python-Dependencies für Dokumenten-Parser..."
pip install --quiet --upgrade \
    pdfplumber \
    PyMuPDF \
    python-docx \
    openpyxl \
    oletools \
    pytesseract \
    Pillow \
    pandas \
    tabulate
ok "Python-Dependencies installiert"

# 5. Tesseract OCR (für Bild-/Scan-Erkennung)
echo ""
echo "5. Prüfe Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    ok "Tesseract gefunden: $(tesseract --version 2>&1 | head -1)"
else
    warn "Tesseract nicht gefunden, installiere..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng
    ok "Tesseract installiert"
fi

# 6. pgvector prüfen (PostgreSQL Extension)
echo ""
echo "6. Prüfe pgvector Extension..."
if command -v psql &> /dev/null; then
    # Versuche Extension zu aktivieren
    PGVECTOR_CHECK=$(psql -U postgres -d flownavigator -c "SELECT extname FROM pg_extension WHERE extname='vector';" 2>/dev/null | grep vector || true)
    if [ -n "$PGVECTOR_CHECK" ]; then
        ok "pgvector bereits aktiviert"
    else
        warn "pgvector nicht aktiviert. Aktiviere manuell:"
        echo "    psql -U postgres -d flownavigator -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    fi
else
    warn "psql nicht gefunden. pgvector manuell prüfen."
fi

# 7. API-Key prüfen
echo ""
echo "7. Prüfe ANTHROPIC_API_KEY..."
if [ -n "$ANTHROPIC_API_KEY" ]; then
    ok "API-Key gesetzt (${ANTHROPIC_API_KEY:0:10}...)"
else
    warn "ANTHROPIC_API_KEY nicht gesetzt!"
    echo ""
    echo "   Bitte in ~/.bashrc oder ~/.zshrc hinzufügen:"
    echo "   export ANTHROPIC_API_KEY=\"sk-ant-...\""
    echo ""
fi

# 8. .claude Verzeichnis prüfen
echo ""
echo "8. Prüfe .claude Konfiguration..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -d "$PROJECT_DIR/.claude/commands" ]; then
    COMMAND_COUNT=$(find "$PROJECT_DIR/.claude/commands" -name "*.md" | wc -l)
    ok ".claude/commands vorhanden ($COMMAND_COUNT Commands)"
else
    fail ".claude/commands nicht gefunden. Bitte Repository neu klonen."
fi

echo ""
echo "=========================================="
echo "  Setup abgeschlossen!"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo ""
echo "  1. API-Key setzen (falls noch nicht geschehen):"
echo "     export ANTHROPIC_API_KEY=\"sk-ant-...\""
echo ""
echo "  2. Claude CLI starten:"
echo "     cd $PROJECT_DIR"
echo "     claude"
echo ""
echo "  3. Verfügbare Commands:"
echo "     /phase <n>         - Phase n implementieren"
echo "     /implement <task>  - Spezifischen Task implementieren"
echo "     /dev:service <n>   - Service erstellen"
echo "     /dev:parser <fmt>  - Parser erstellen (pdf, docx, xlsx...)"
echo "     /dev:endpoint <p>  - API-Endpoint erstellen"
echo "     /dev:model <n>     - SQLAlchemy Model erstellen"
echo "     /test <scope>      - Tests ausführen"
echo "     /review <path>     - Code-Review"
echo ""
echo "  4. Starte mit Phase 1:"
echo "     /phase 1"
echo ""
