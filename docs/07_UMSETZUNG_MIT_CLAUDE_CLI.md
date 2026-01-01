# Umsetzung des Development-Moduls mit Claude Code CLI

> Praktische Anleitung zur Implementierung mit Agents, Subagents und Custom Commands

---

## 1. Grundlagen: Claude Code CLI

### 1.1 Was ist Claude Code CLI?

Claude Code CLI (`claude`) ist ein Terminal-basiertes KI-Tool für Software-Entwicklung. Es kann:
- Code lesen, schreiben und bearbeiten
- Befehle ausführen (git, npm, pytest, etc.)
- Dateien suchen und analysieren
- Komplexe Tasks in Subtasks aufteilen (Agents)

### 1.2 Installation & Setup

```bash
# Installation (global)
npm install -g @anthropic-ai/claude-code

# Oder mit pnpm
pnpm add -g @anthropic-ai/claude-code

# API-Key konfigurieren
export ANTHROPIC_API_KEY="sk-ant-..."

# In Projektverzeichnis starten
cd /home/user/flownavigator
claude
```

### 1.3 Projekt-Konfiguration

Erstelle `.claude/settings.json` im Projektroot:

```json
{
  "model": "claude-sonnet-4-20250514",
  "permissions": {
    "allow_bash": true,
    "allow_file_write": true,
    "allow_file_read": true
  },
  "context": {
    "include": [
      "docs/05_KONZEPT_DEVELOPMENT_MODUL.md",
      "docs/06_UMSETZUNGSPLAN_DEVELOPMENT_MODUL.md"
    ]
  }
}
```

---

## 2. Agents und Subagents

### 2.1 Was sind Agents?

**Agents** sind spezialisierte Instanzen, die Claude für komplexe, mehrstufige Aufgaben startet. Sie arbeiten autonom und berichten am Ende zurück.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENT-ARCHITEKTUR                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                        ┌─────────────────────┐                                  │
│                        │   HAUPT-CLAUDE      │                                  │
│                        │   (Orchestrator)    │                                  │
│                        └──────────┬──────────┘                                  │
│                                   │                                              │
│              ┌────────────────────┼────────────────────┐                        │
│              │                    │                    │                        │
│              ▼                    ▼                    ▼                        │
│     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│     │   EXPLORE       │  │     PLAN        │  │  GENERAL        │              │
│     │   Agent         │  │     Agent       │  │  PURPOSE        │              │
│     ├─────────────────┤  ├─────────────────┤  ├─────────────────┤              │
│     │ • Glob          │  │ • Glob          │  │ • Alle Tools    │              │
│     │ • Grep          │  │ • Grep          │  │ • Bash          │              │
│     │ • Read          │  │ • Read          │  │ • Edit          │              │
│     │                 │  │ • Write         │  │ • Write         │              │
│     │ Schnelle        │  │ Erstellt        │  │ Komplexe        │              │
│     │ Codebase-       │  │ Implementierungs│  │ Multi-Step      │              │
│     │ Erkundung       │  │ pläne           │  │ Tasks           │              │
│     └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent-Typen in Claude Code

| Agent-Typ | Beschreibung | Tools | Verwendung |
|-----------|--------------|-------|------------|
| **Explore** | Schnelle Codebase-Erkundung | Glob, Grep, Read | "Wo sind die API-Endpoints?" |
| **Plan** | Architektur-Planung | Alle + Read/Write | "Plane die Implementierung" |
| **General-Purpose** | Komplexe Tasks | Alle Tools | Multi-Step Implementierung |

### 2.3 Wann Agents verwenden?

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ENTSCHEIDUNGSBAUM: AGENT ODER DIREKT?                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Aufgabe bekommen                                                                │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────────────────────┐                                                │
│  │ Weiß ich genau, welche     │                                                │
│  │ Datei ich bearbeiten muss? │                                                │
│  └─────────────────────────────┘                                                │
│       │                                                                          │
│       ├── JA ──► Direkt mit Read/Edit arbeiten                                  │
│       │                                                                          │
│       └── NEIN                                                                   │
│            │                                                                     │
│            ▼                                                                     │
│       ┌─────────────────────────────┐                                           │
│       │ Muss ich erst suchen,       │                                           │
│       │ wo etwas ist?               │                                           │
│       └─────────────────────────────┘                                           │
│            │                                                                     │
│            ├── JA ──► EXPLORE Agent ("quick"/"medium"/"thorough")               │
│            │                                                                     │
│            └── NEIN                                                              │
│                 │                                                                │
│                 ▼                                                                │
│            ┌─────────────────────────────┐                                      │
│            │ Muss ich einen Plan         │                                      │
│            │ erstellen?                  │                                      │
│            └─────────────────────────────┘                                      │
│                 │                                                                │
│                 ├── JA ──► PLAN Agent                                           │
│                 │                                                                │
│                 └── NEIN ──► GENERAL-PURPOSE Agent                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Praktische Agent-Beispiele

#### Explore Agent - Codebase verstehen

```
User: "Wo werden im Backend die Tenants verwaltet?"

Claude denkt: "Ich muss die Codebase durchsuchen"
→ Startet EXPLORE Agent mit "medium" Thoroughness
→ Agent sucht nach "tenant" in models, api, services
→ Agent meldet zurück: "Tenants in app/models/tenant.py, API in app/api/tenants.py"
```

#### Plan Agent - Implementierung planen

```
User: "Plane die Implementierung des Document-Parser-Service"

Claude denkt: "Komplexer Task, braucht Architektur-Analyse"
→ Startet PLAN Agent
→ Agent analysiert bestehende Services
→ Agent erstellt Plan mit Schritten
→ Schreibt Plan in Datei
→ Fragt User um Freigabe
```

#### General-Purpose Agent - Implementieren

```
User: "Implementiere parse_pdf() nach dem Konzept"

Claude denkt: "Konkreter Implementierungs-Task"
→ Startet GENERAL-PURPOSE Agent
→ Agent liest Konzept
→ Agent erstellt/bearbeitet Datei
→ Agent führt Tests aus
→ Meldet Ergebnis zurück
```

---

## 3. Subagents (Parallele Ausführung)

### 3.1 Was sind Subagents?

Subagents sind **parallel laufende** Agent-Instanzen für unabhängige Teilaufgaben.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SUBAGENT-PARALLELISIERUNG                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  User: "Implementiere die Parser für PDF, DOCX und XLSX"                        │
│                                                                                  │
│                        ┌─────────────────────┐                                  │
│                        │   HAUPT-CLAUDE      │                                  │
│                        │   (Orchestrator)    │                                  │
│                        └──────────┬──────────┘                                  │
│                                   │                                              │
│                      PARALLEL LAUNCH (gleichzeitig!)                            │
│              ┌────────────────────┼────────────────────┐                        │
│              │                    │                    │                        │
│              ▼                    ▼                    ▼                        │
│     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│     │   Subagent 1    │  │   Subagent 2    │  │   Subagent 3    │              │
│     │   parse_pdf()   │  │   parse_docx()  │  │   parse_xlsx()  │              │
│     │                 │  │                 │  │                 │              │
│     │ • pdfplumber    │  │ • python-docx   │  │ • openpyxl      │              │
│     │ • OCR logic     │  │ • Tabellen      │  │ • Sheets        │              │
│     │ • Tests         │  │ • Tests         │  │ • Tests         │              │
│     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│              │                    │                    │                        │
│              └────────────────────┼────────────────────┘                        │
│                                   │                                              │
│                                   ▼                                              │
│                        ┌─────────────────────┐                                  │
│                        │   ERGEBNISSE        │                                  │
│                        │   ZUSAMMENFÜHREN    │                                  │
│                        └─────────────────────┘                                  │
│                                                                                  │
│  Zeit: ~3 Minuten (statt ~9 Minuten sequentiell)                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Wann Subagents verwenden?

| Situation | Subagents? | Beispiel |
|-----------|------------|----------|
| Unabhängige Dateien | ✅ JA | PDF-Parser + XLSX-Parser parallel |
| Sequentielle Abhängigkeit | ❌ NEIN | Erst Model, dann Service |
| Parallele Tests | ✅ JA | Unit-Tests + E2E-Tests gleichzeitig |
| Code-Review | ✅ JA | Frontend + Backend parallel reviewen |

### 3.3 Praktisches Subagent-Beispiel

```
User: "Implementiere alle Parser parallel"

Claude:
"Ich starte 3 Subagents parallel für maximale Effizienz:"

[Subagent 1: PDF-Parser]
- Liest Konzept Sektion 3.4
- Erstellt apps/backend/app/services/development/parsers/pdf_parser.py
- Schreibt Tests
- Meldet: "PDF-Parser fertig, 8 Tests grün"

[Subagent 2: DOCX-Parser]  (parallel!)
- Liest Konzept Sektion 3.4
- Erstellt apps/backend/app/services/development/parsers/docx_parser.py
- Schreibt Tests
- Meldet: "DOCX-Parser fertig, 6 Tests grün"

[Subagent 3: XLSX-Parser]  (parallel!)
- Liest Konzept Sektion 3.4
- Erstellt apps/backend/app/services/development/parsers/xlsx_parser.py
- Schreibt Tests
- Meldet: "XLSX-Parser fertig, 10 Tests grün"

Claude:
"Alle 3 Parser implementiert. Gesamtzeit: 3:24 Minuten.
24 Tests insgesamt, alle grün."
```

---

## 4. Custom Slash Commands

### 4.1 Was sind Slash Commands?

Slash Commands sind **wiederverwendbare Prompts**, die du mit `/befehl` aufrufst.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SLASH COMMAND STRUKTUR                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  .claude/                                                                        │
│  └── commands/                                                                   │
│      ├── implement.md         →  /implement <task>                              │
│      ├── test.md              →  /test <file>                                   │
│      ├── review.md            →  /review <file>                                 │
│      ├── phase.md             →  /phase <nummer>                                │
│      └── dev/                                                                    │
│          ├── parser.md        →  /dev:parser <format>                           │
│          ├── service.md       →  /dev:service <name>                            │
│          └── endpoint.md      →  /dev:endpoint <path>                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Command-Syntax

Commands sind Markdown-Dateien mit Platzhaltern:

```markdown
<!-- .claude/commands/implement.md -->

Implementiere den folgenden Task aus dem Umsetzungsplan:

**Task:** $ARGUMENTS

**Vorgehen:**
1. Lies das Konzept in `docs/05_KONZEPT_DEVELOPMENT_MODUL.md`
2. Lies den Umsetzungsplan in `docs/06_UMSETZUNGSPLAN_DEVELOPMENT_MODUL.md`
3. Finde den entsprechenden Abschnitt für "$ARGUMENTS"
4. Implementiere nach den Anforderungen
5. Schreibe Tests
6. Führe die Tests aus
7. Committe mit aussagekräftiger Message

**Wichtig:**
- Halte dich EXAKT an die Pfadstruktur im Konzept
- Nutze die vorhandenen Patterns der Codebase
- Keine zusätzlichen Features ohne Anforderung
```

**Verwendung:**
```
/implement Document-Parser-Service
```

### 4.3 Empfohlene Commands für dieses Projekt

Ich erstelle jetzt die wichtigsten Commands:

---

## 5. Projekt-spezifische Commands

### 5.1 /phase - Implementiere eine Phase

```markdown
<!-- .claude/commands/phase.md -->

Implementiere Phase $ARGUMENTS aus dem Umsetzungsplan.

**Schritte:**
1. Öffne `docs/06_UMSETZUNGSPLAN_DEVELOPMENT_MODUL.md`
2. Finde "## Phase $ARGUMENTS"
3. Liste alle Tasks dieser Phase auf
4. Implementiere jeden Task sequentiell
5. Markiere erledigte Tasks mit [x]
6. Führe nach jedem Task die relevanten Tests aus
7. Committe nach jeder abgeschlossenen Sektion

**Ausgabe:**
- Zusammenfassung der implementierten Tasks
- Testergebnisse
- Commit-Hashes
```

### 5.2 /dev:service - Erstelle einen Service

```markdown
<!-- .claude/commands/dev/service.md -->

Erstelle den Service "$ARGUMENTS" nach dem Development-Modul Konzept.

**Pfad:** `apps/backend/app/services/development/$ARGUMENTS.py`

**Schritte:**
1. Lies das Konzept für diesen Service
2. Prüfe existierende Services als Referenz:
   - `apps/backend/app/services/module_service.py`
   - `apps/backend/app/services/llm/`
3. Erstelle den Service mit:
   - Typ-Annotationen
   - Docstrings
   - Async/await wo nötig
   - Dependency Injection via __init__
4. Erstelle Tests in `apps/backend/tests/services/development/test_$ARGUMENTS.py`
5. Führe Tests aus: `pytest apps/backend/tests/services/development/test_$ARGUMENTS.py -v`

**Patterns:**
- SQLAlchemy async session
- Pydantic für Schemas
- Logger pro Service
```

### 5.3 /dev:parser - Erstelle einen Dokumenten-Parser

```markdown
<!-- .claude/commands/dev/parser.md -->

Erstelle den Parser für Format "$ARGUMENTS" gemäß Konzept Sektion 3.4.

**Pfad:** `apps/backend/app/services/development/parsers/$ARGUMENTS_parser.py`

**Unterstützte Formate:**
- pdf → pdfplumber + OCR
- docx → python-docx
- docm → python-docx + oletools
- xlsx → openpyxl
- xlsm → openpyxl + oletools
- image → pytesseract + PIL

**Schritte:**
1. Lies Konzept Sektion 3.4 "Dokumenten-Parsing"
2. Implementiere die `parse_$ARGUMENTS()` Methode
3. Erstelle `ParseResult` mit content, tables, metadata
4. Für Makro-Dateien: Sicherheitswarnung hinzufügen
5. Schreibe Tests mit Beispiel-Dateien
6. Führe Tests aus

**Sicherheit:**
- VBA-Makros NUR extrahieren, NIEMALS ausführen
- Warnung bei Shell/Network/Registry-Aufrufen
```

### 5.4 /dev:endpoint - Erstelle API-Endpoint

```markdown
<!-- .claude/commands/dev/endpoint.md -->

Erstelle den API-Endpoint "$ARGUMENTS" für das Development-Modul.

**Pfad:** `apps/backend/app/api/development.py`

**Schritte:**
1. Prüfe existierende Endpoints als Referenz:
   - `apps/backend/app/api/modules.py`
   - `apps/backend/app/api/document_box.py`
2. Erstelle den Endpoint mit:
   - Korrektem HTTP-Verb (GET/POST/PUT/DELETE)
   - Pydantic Request/Response Schemas
   - Authentifizierung via `get_current_user`
   - Tenant-Filterung
   - Audit-Logging
3. Registriere in `apps/backend/app/api/__init__.py` falls nötig
4. Erstelle Test in `apps/backend/tests/api/test_development.py`
5. Teste mit pytest

**Patterns:**
- FastAPI Router
- Dependency Injection
- HTTPException für Fehler
- Background Tasks für lange Operationen
```

### 5.5 /test - Führe Tests aus

```markdown
<!-- .claude/commands/test.md -->

Führe Tests aus für: $ARGUMENTS

**Mögliche Argumente:**
- `all` → Alle Tests
- `backend` → Nur Backend-Tests
- `frontend` → Nur Frontend-Tests
- `development` → Nur Development-Modul Tests
- `<dateiname>` → Spezifische Testdatei

**Befehle:**
- Backend: `pytest apps/backend/tests/ -v --tb=short`
- Frontend: `cd apps/frontend && pnpm test`
- Spezifisch: `pytest $ARGUMENTS -v`

**Bei Fehlern:**
1. Analysiere die Fehlermeldung
2. Finde die betroffene Datei
3. Schlage Fix vor
4. Frage ob Fix angewendet werden soll
```

### 5.6 /review - Code-Review

```markdown
<!-- .claude/commands/review.md -->

Führe ein Code-Review durch für: $ARGUMENTS

**Prüfpunkte:**
1. **Architektur-Konsistenz**
   - Pfade nach Projekt-Pattern?
   - Imports korrekt?

2. **Code-Qualität**
   - Typ-Annotationen vorhanden?
   - Docstrings?
   - Error-Handling?

3. **Sicherheit**
   - SQL-Injection möglich?
   - XSS-Risiken?
   - Secrets im Code?

4. **Tests**
   - Ausreichende Testabdeckung?
   - Edge-Cases abgedeckt?

5. **Performance**
   - N+1 Queries?
   - Unnötige Loops?

**Ausgabe:**
- Liste der Findings (Severity: critical/warning/info)
- Vorgeschlagene Fixes
- Lob für gute Patterns
```

---

## 6. Workflow: Development-Modul implementieren

### 6.1 Empfohlene Reihenfolge

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTIERUNGS-WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Tag 1: Infrastruktur                                                           │
│  ─────────────────────                                                          │
│  /phase 1                    → pgvector, Package-Struktur                       │
│  /phase 2                    → Datenmodelle, Migrationen                        │
│                                                                                  │
│  Tag 2: Core Services                                                           │
│  ────────────────────                                                           │
│  /dev:service session_service                                                   │
│  /dev:parser pdf             ┐                                                  │
│  /dev:parser docx            │ PARALLEL mit Subagents                          │
│  /dev:parser xlsx            ┘                                                  │
│  /dev:service feedback_service                                                  │
│                                                                                  │
│  Tag 3: LLM & Architecture                                                      │
│  ─────────────────────────                                                      │
│  /dev:service llm_orchestrator                                                  │
│  /dev:service architecture_scanner                                              │
│  /dev:service consistency_checker                                               │
│                                                                                  │
│  Tag 4: API & Frontend                                                          │
│  ─────────────────────                                                          │
│  /dev:endpoint sessions      ┐                                                  │
│  /dev:endpoint files         │ Sequentiell (Abhängigkeiten)                    │
│  /dev:endpoint feedback      ┘                                                  │
│  Frontend-Komponenten                                                           │
│                                                                                  │
│  Tag 5: Integration & Tests                                                     │
│  ─────────────────────────                                                      │
│  /test development                                                              │
│  /review apps/backend/app/services/development/                                 │
│  E2E-Tests                                                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Beispiel-Session

```bash
# Terminal 1: Claude starten
cd /home/user/flownavigator
claude

# In Claude:
> /phase 1

Claude: "Ich implementiere Phase 1: Basis-Infrastruktur

[1/3] pgvector Extension...
Führe aus: CREATE EXTENSION IF NOT EXISTS vector;
✓ Extension aktiviert

[2/3] Package-Struktur...
Erstelle packages/domain/development/
Erstelle package.json, tsconfig.json, src/index.ts
✓ @flowaudit/development Package erstellt

[3/3] Backend-Modul-Struktur...
Erstelle apps/backend/app/api/development.py
Erstelle apps/backend/app/services/development/__init__.py
✓ Backend-Struktur erstellt

Phase 1 abgeschlossen. Commit erstellt: abc123"

> /dev:parser pdf

Claude: "Implementiere PDF-Parser...

Lese Konzept Sektion 3.4...
Erstelle apps/backend/app/services/development/parsers/pdf_parser.py

[Parser erstellt mit:]
- parse_pdf() mit pdfplumber
- OCR-Fallback für Scans
- Tabellen-Extraktion
- ParseResult Rückgabe

Schreibe Tests...
Führe aus: pytest tests/services/development/parsers/test_pdf_parser.py -v

✓ 8/8 Tests bestanden

Commit: 'feat(development): add PDF parser with OCR support'"
```

---

## 7. Best Practices

### 7.1 Effiziente Prompts

| Schlecht ❌ | Gut ✅ |
|-------------|--------|
| "Mach mal den Parser" | "/dev:parser pdf" |
| "Irgendwas mit Tests" | "/test development" |
| "Schau mal ob das passt" | "/review apps/backend/app/services/development/" |

### 7.2 Kontext nutzen

```bash
# Konzept als Kontext laden
claude --context docs/05_KONZEPT_DEVELOPMENT_MODUL.md

# Oder in .claude/settings.json permanent konfigurieren
```

### 7.3 Checkpoints

Nach jeder abgeschlossenen Phase:
1. Tests ausführen
2. Code-Review machen
3. Committen
4. Status dokumentieren

### 7.4 Fehler-Handling

```
User: /dev:service xyz_service
Claude: "Fehler: xyz_service nicht im Konzept gefunden.

Verfügbare Services:
- session_service (Phase 3.1)
- document_parser (Phase 3.2)
- feedback_service (Phase 3.3)
- architecture_scanner (Phase 3.4)
..."
```

---

## 8. Quick Reference

### 8.1 Alle Commands

| Command | Beschreibung |
|---------|--------------|
| `/phase <n>` | Implementiere Phase n aus Umsetzungsplan |
| `/dev:service <name>` | Erstelle Backend-Service |
| `/dev:parser <format>` | Erstelle Dokumenten-Parser |
| `/dev:endpoint <path>` | Erstelle API-Endpoint |
| `/test <scope>` | Führe Tests aus |
| `/review <path>` | Code-Review |

### 8.2 Agent-Auswahl

| Situation | Agent | Prompt-Beispiel |
|-----------|-------|-----------------|
| "Wo ist...?" | Explore | "Wo werden Tenants definiert?" |
| "Plane..." | Plan | "Plane die Migration zu pgvector" |
| "Implementiere..." | General | "/dev:service session_service" |
| "Parallel..." | Subagents | "Implementiere alle Parser parallel" |

### 8.3 Wichtige Dateien

```
docs/05_KONZEPT_DEVELOPMENT_MODUL.md    # WAS zu bauen ist
docs/06_UMSETZUNGSPLAN_DEVELOPMENT_MODUL.md  # WIE zu bauen ist
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md     # MIT WAS zu bauen ist
.claude/commands/                        # Custom Commands
```

---

## 9. Troubleshooting

### 9.1 "Agent antwortet nicht"

```bash
# Timeout erhöhen
claude --timeout 300

# Oder in Settings:
{
  "timeout": 300000
}
```

### 9.2 "Falscher Pfad erstellt"

Immer das Konzept als Kontext laden:
```bash
claude --context docs/05_KONZEPT_DEVELOPMENT_MODUL.md
```

### 9.3 "Tests schlagen fehl nach Änderung"

```
/test development
# Analysiert Fehler und schlägt Fixes vor
```

---

## 10. Nächste Schritte

1. **Commands einrichten:**
   ```bash
   mkdir -p .claude/commands/dev
   # Commands aus diesem Dokument erstellen
   ```

2. **Phase 1 starten:**
   ```bash
   claude
   > /phase 1
   ```

3. **Iterativ vorgehen:**
   - Eine Phase nach der anderen
   - Tests nach jedem Schritt
   - Reviews vor Commits

---

*Dieses Dokument dient als praktische Referenz für die Implementierung mit Claude Code CLI.*
