# Konzept: Development-Modul mit iterativem Workflow und Memory

## 1. Übersicht

Das Development-Modul ist das zentrale Werkzeug zur Entwicklung neuer Module und Features. Es kombiniert:

- **Modul-Auswahl** mit Flussdiagramm-Visualisierung
- **Iterativen Feedback-Loop** zwischen Entwickler und LLM
- **Persistentes Memory** für Kontext über Sessions hinweg
- **Parallele Entwicklung und Testing**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT-MODUL WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │ 1. MODUL     │───>│ 2. DATEIEN   │───>│ 3. AUFGABE BESCHREIBEN          │   │
│  │    AUSWÄHLEN │    │    HOCHLADEN │    │    (Was soll entwickelt werden?) │   │
│  └──────────────┘    └──────────────┘    └──────────────────────────────────┘   │
│         │                   │                           │                        │
│         ▼                   ▼                           ▼                        │
│  ┌──────────────┐    ┌──────────────┐    ╔══════════════════════════════════╗   │
│  │ Flussdiagramm│    │ Erläuterung  │    ║ 4. ITERATIVER FEEDBACK-LOOP     ║   │
│  │ zeigt        │    │ pro Datei    │    ║    ┌───────────────────────┐    ║   │
│  │ Position     │    │ eingeben     │    ║    │ LLM → Vorschlag       │    ║   │
│  └──────────────┘    └──────────────┘    ║    │      ↓                │    ║   │
│                                          ║    │ User → Feedback       │    ║   │
│                                          ║    │      ↓                │    ║   │
│                                          ║    │ LLM → Überarbeitung   │    ║   │
│                                          ║    │      ↓                │    ║   │
│                                          ║    │ Wiederholen...        │    ║   │
│                                          ║    └───────────────────────┘    ║   │
│                                          ╚══════════════════════════════════╝   │
│                                                         │                        │
│                                                         ▼                        │
│                                          ┌──────────────────────────────────┐   │
│                                          │ 5. FREIGABE                      │   │
│                                          │    User gibt Entwicklung frei    │   │
│                                          └──────────────────────────────────┘   │
│                                                         │                        │
│                                                         ▼                        │
│                                          ┌──────────────────────────────────┐   │
│                                          │ 6. ENTWICKLUNG + TESTING         │   │
│                                          │    (parallel)                    │   │
│                                          └──────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: Modul-Auswahl

### 2.1 Zwei Modi

| Modus | Beschreibung | Ergebnis |
|-------|--------------|----------|
| **Bestehendes Modul** | Feature für existierendes Modul → Neue Version | `version: 1.2.0 → 1.3.0` |
| **Neues Modul** | Komplett neues Modul erstellen | Neuer Eintrag im Flussdiagramm |

### 2.2 Flussdiagramm der Module

Das Flussdiagramm zeigt alle Module und ihre Beziehungen. Der User wählt:
- Bei **bestehendem Modul**: Das Modul im Diagramm anklicken
- Bei **neuem Modul**: Position im Workflow festlegen (vor/nach welchem Modul?)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MODULE WORKFLOW DIAGRAM                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐   │
│    │  Common    │─────>│ Validation │─────>│ Checklists │─────>│ Group      │   │
│    │  v2.1.0    │      │  v1.4.0    │      │  v3.2.0    │      │ Queries    │   │
│    └────────────┘      └────────────┘      └────────────┘      │  v1.1.0    │   │
│          │                                       │              └────────────┘   │
│          │                                       │                    │          │
│          ▼                                       ▼                    ▼          │
│    ┌────────────┐                         ┌────────────┐      ┌────────────┐    │
│    │ Vue-Adapter│                         │ Document   │─────>│ Reports    │    │
│    │  v2.0.0    │                         │ Box v1.5.0 │      │  v1.0.0    │    │
│    └────────────┘                         └────────────┘      └────────────┘    │
│                                                                                  │
│    ─────────────────────────────────────────────────────────────────────────    │
│    Legende:                                                                      │
│    ┌────────────┐  Modul mit Version                                            │
│    │  [Name]    │  ───> Abhängigkeit                                            │
│    │  v[x.y.z]  │  ● Ausgewähltes Modul                                         │
│    └────────────┘                                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Datenmodell: Module Registry

```sql
CREATE TABLE module_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Identifikation
    name VARCHAR(100) NOT NULL,              -- z.B. "checklists"
    display_name VARCHAR(255) NOT NULL,      -- z.B. "Checklisten-Modul"
    package_name VARCHAR(255) NOT NULL,      -- z.B. "@flowaudit/checklists"

    -- Version
    current_version VARCHAR(20) NOT NULL,    -- z.B. "3.2.0"

    -- Workflow-Position
    workflow_position INTEGER NOT NULL,      -- Reihenfolge im Fluss
    workflow_group VARCHAR(50),              -- z.B. "core", "domain", "reporting"

    -- Abhängigkeiten (als JSON Array von module_ids)
    dependencies JSONB DEFAULT '[]',
    dependents JSONB DEFAULT '[]',           -- Module die von diesem abhängen

    -- Status
    status VARCHAR(20) DEFAULT 'active',     -- active, deprecated, development

    -- Metadaten
    description TEXT,
    icon VARCHAR(50),                        -- Icon für Flussdiagramm
    color VARCHAR(20),                       -- Farbe für Flussdiagramm

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

-- Versions-Historie
CREATE TABLE module_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES module_registry(id) ON DELETE CASCADE,

    version VARCHAR(20) NOT NULL,
    release_notes TEXT,
    changelog JSONB DEFAULT '[]',

    -- Entwicklungs-Referenz
    development_session_id UUID,             -- Verweis auf die Development-Session

    released_at TIMESTAMP,
    released_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. Phase 2: Dateien hochladen mit Erläuterungen

### 3.1 Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DATEI-UPLOAD MIT ERLÄUTERUNGEN                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Hochgeladene Dateien                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  📄 anforderungen.xlsx                                          [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: Diese Excel enthält alle fachlichen Anforderungen │    │    │
│  │  │ für die neue Prüfungslogik. Spalte A = ID, Spalte B = Text...  │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  📄 current_implementation.py                                    [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: Aktuelle Implementierung des ChecklistAnalyzer.   │    │    │
│  │  │ Muss erweitert werden um die neuen Prüfregeln zu unterstützen. │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  📄 api_spec.yaml                                                [✓]     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ Erläuterung: OpenAPI-Spec der externen API die angebunden      │    │    │
│  │  │ werden soll. Wichtig: Authentifizierung per Bearer Token.      │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  │                                                                          │    │
│  │  [+ Weitere Datei hochladen]                                            │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Weiter: Aufgabe beschreiben →]                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Datenmodell: Dateien mit Erläuterungen

```sql
CREATE TABLE development_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    -- Datei-Info
    original_filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),

    -- Erläuterung durch User
    user_annotation TEXT NOT NULL,           -- Pflichtfeld!
    annotation_language VARCHAR(10) DEFAULT 'de',

    -- Verarbeitung
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    parsed_content TEXT,                     -- Extrahierter Text-Inhalt
    parsed_metadata JSONB DEFAULT '{}',      -- Zusätzliche Metadaten (Spalten, Struktur, etc.)

    -- Embedding für RAG
    embedding_status VARCHAR(20) DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,

    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Datei-Chunks für RAG
CREATE TABLE development_file_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES development_files(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,

    -- Optional: Embedding Vector (wenn pgvector installiert)
    -- embedding vector(1536),

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Phase 3: Aufgabe beschreiben

### 4.1 Aufgaben-Template

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AUFGABE BESCHREIBEN                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Modul: @flowaudit/checklists (v3.2.0 → v3.3.0)                                 │
│  Position im Workflow: Nach "Validation", vor "Document Box"                    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Aufgabenbeschreibung                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ Ich möchte eine neue Prüfungslogik implementieren, die:                 │    │
│  │                                                                          │    │
│  │ 1. Die Anforderungen aus anforderungen.xlsx automatisch einliest        │    │
│  │ 2. Für jede Anforderung eine Prüfregel erstellt                         │    │
│  │ 3. Die Prüfregeln gegen hochgeladene Dokumente validiert                │    │
│  │ 4. Einen Bericht mit Findings erstellt                                  │    │
│  │                                                                          │    │
│  │ Wichtig:                                                                 │    │
│  │ - Muss kompatibel sein mit der bestehenden ChecklistAnalyzer API        │    │
│  │ - Soll die externe API (siehe api_spec.yaml) für zusätzliche Daten      │    │
│  │   nutzen können                                                          │    │
│  │ - Performance: Max. 2 Sekunden pro Dokument                             │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  Kategorie: [Feature ▾]    Priorität: [Hoch ▾]                                  │
│                                                                                  │
│  [LLM-Analyse starten →]                                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Datenmodell: Development Session

```sql
CREATE TABLE development_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Modul-Referenz
    module_id UUID REFERENCES module_registry(id),
    is_new_module BOOLEAN DEFAULT FALSE,
    new_module_name VARCHAR(100),            -- Falls neues Modul

    -- Version
    base_version VARCHAR(20),                -- Ausgangs-Version (z.B. "3.2.0")
    target_version VARCHAR(20),              -- Ziel-Version (z.B. "3.3.0")

    -- Aufgabe
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT NOT NULL,
    task_category VARCHAR(50),               -- feature, bugfix, refactoring, enhancement
    task_priority VARCHAR(20),               -- low, medium, high, critical

    -- Status
    status VARCHAR(30) DEFAULT 'draft',      -- draft, analyzing, feedback_loop, approved, developing, testing, completed
    current_iteration INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- User
    created_by VARCHAR(100),
    approved_by VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index für schnelle Suche
CREATE INDEX idx_dev_sessions_module ON development_sessions(module_id);
CREATE INDEX idx_dev_sessions_status ON development_sessions(status);
```

---

## 5. Phase 4: Iterativer Feedback-Loop

### 5.1 Der Kern des Systems

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ITERATIVER FEEDBACK-LOOP                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Iteration #3                                                    [History ▾]    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LLM-VORSCHLAG                                                           │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ ## Implementierungsplan v3                                              │    │
│  │                                                                          │    │
│  │ ### 1. Neue Komponenten                                                 │    │
│  │                                                                          │    │
│  │ **RequirementParser** (services/requirement_parser.py)                  │    │
│  │ - Liest XLSX mit openpyxl                                               │    │
│  │ - Validiert Spaltenstruktur (ID, Text, Kategorie)                       │    │
│  │ - Gibt List[Requirement] zurück                                         │    │
│  │                                                                          │    │
│  │ **RuleGenerator** (services/rule_generator.py)                          │    │
│  │ - Transformiert Requirement → PrüfRegel                                 │    │
│  │ - Nutzt LLM für komplexe Regel-Interpretation                          │    │
│  │ - Cacht generierte Regeln                                               │    │
│  │                                                                          │    │
│  │ **ExternalAPIClient** (clients/external_api.py)                         │    │
│  │ - Implementiert api_spec.yaml                                           │    │
│  │ - Bearer Token Auth                                                     │    │
│  │ - Rate Limiting (100 req/min)                                           │    │
│  │                                                                          │    │
│  │ ### 2. API-Endpunkte                                                    │    │
│  │ - POST /api/v1/checklists/{id}/import-requirements                     │    │
│  │ - POST /api/v1/checklists/{id}/validate-document                       │    │
│  │ - GET /api/v1/checklists/{id}/findings                                 │    │
│  │                                                                          │    │
│  │ ### 3. Datenbank-Änderungen                                             │    │
│  │ - Neue Tabelle: checklist_requirements                                  │    │
│  │ - Neue Tabelle: checklist_rules                                         │    │
│  │ - Neue Tabelle: validation_findings                                     │    │
│  │                                                                          │    │
│  │ [Vollständigen Plan anzeigen...]                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ IHR FEEDBACK                                                            │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ Der Plan sieht gut aus! Aber:                                           │    │
│  │                                                                          │    │
│  │ 1. Der ExternalAPIClient sollte async sein für bessere Performance      │    │
│  │ 2. Bitte auch Fehlerbehandlung für ungültige XLSX-Dateien einplanen     │    │
│  │ 3. Die Findings sollten einen Schweregrad haben (info, warning, error)  │    │
│  │                                                                          │    │
│  │ Ansonsten kann ich so freigeben.                                        │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [← Vorherige Iteration]  [Feedback senden]  [✓ Freigeben →]                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Datenmodell: Iterationen

```sql
-- Vorschlags-Iterationen
CREATE TABLE development_iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    iteration_number INTEGER NOT NULL,

    -- LLM-Vorschlag
    proposal_type VARCHAR(50) NOT NULL,      -- analysis, implementation_plan, code_review
    proposal_content TEXT NOT NULL,          -- Markdown-formatierter Vorschlag
    proposal_structured JSONB DEFAULT '{}',  -- Strukturierte Daten (Komponenten, APIs, etc.)

    -- LLM-Metadaten
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    llm_tokens_used INTEGER DEFAULT 0,
    llm_latency_ms INTEGER,
    llm_prompt TEXT,                         -- Der verwendete Prompt (für Debugging)

    -- User-Feedback
    feedback_content TEXT,                   -- Freitext-Feedback
    feedback_rating INTEGER,                 -- 1-5 Sterne (optional)
    feedback_tags JSONB DEFAULT '[]',        -- ["zu_komplex", "fehler", "unvollständig"]
    feedback_at TIMESTAMP,
    feedback_by VARCHAR(100),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',    -- pending, feedback_received, revised, approved

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_iterations_session ON development_iterations(session_id, iteration_number);
```

### 5.3 Feedback-Tags (vordefiniert)

| Tag | Beschreibung | Auswirkung auf nächste Iteration |
|-----|--------------|-----------------------------------|
| `zu_komplex` | Lösung ist zu kompliziert | LLM soll vereinfachen |
| `zu_einfach` | Lösung deckt nicht alle Fälle ab | LLM soll Details hinzufügen |
| `fehler` | Technischer Fehler im Vorschlag | LLM soll korrigieren |
| `unvollständig` | Aspekte fehlen | LLM soll ergänzen |
| `performance` | Performance-Bedenken | LLM soll optimieren |
| `sicherheit` | Sicherheitsbedenken | LLM soll absichern |
| `inkompatibel` | Passt nicht zur Architektur | LLM soll anpassen |

---

## 6. Memory-System (LLM-Kontext)

### 6.1 Kernprinzip

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY = KONTEXT                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Jede LLM-Anfrage bekommt automatisch relevanten Kontext:                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ KONTEXT-AUFBAU                                                           │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │  1. MODUL-ARCHITEKTUR                                                   │   │
│   │     ├─ Aktuelle Struktur (Komponenten, APIs)                            │   │
│   │     ├─ Tech-Stack (FastAPI, Vue3, PostgreSQL)                           │   │
│   │     └─ Abhängigkeiten zu anderen Modulen                                │   │
│   │                                                                          │   │
│   │  2. HOCHGELADENE DATEIEN + ERLÄUTERUNGEN                                │   │
│   │     ├─ Datei-Inhalt (oder Zusammenfassung bei großen Dateien)           │   │
│   │     └─ User-Erläuterung pro Datei                                       │   │
│   │                                                                          │   │
│   │  3. VORHERIGE ITERATIONEN DIESER SESSION                                │   │
│   │     ├─ Alle bisherigen Vorschläge                                       │   │
│   │     └─ Alle Feedback-Kommentare (KRITISCH!)                             │   │
│   │                                                                          │   │
│   │  4. FRÜHERE KORREKTUREN (aus anderen Sessions)                          │   │
│   │     └─ "Bei ähnlichen Anfragen wurde X korrigiert zu Y"                 │   │
│   │                                                                          │   │
│   │  5. MODUL-HISTORY                                                       │   │
│   │     └─ Letzte Änderungen am Modul                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Datenmodell: Memory

```sql
-- Modul-Architektur (persistentes Wissen über Module)
CREATE TABLE module_architecture (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES module_registry(id) UNIQUE,

    -- Struktur
    description TEXT,
    directory_structure JSONB DEFAULT '{}',
    tech_stack JSONB DEFAULT '{}',           -- {backend: ["FastAPI"], frontend: ["Vue3"]}
    patterns JSONB DEFAULT '[]',             -- ["Service Layer", "Repository"]

    -- Komponenten
    components JSONB DEFAULT '[]',           -- [{name, type, file_path, description}]

    -- Schnittstellen
    api_endpoints JSONB DEFAULT '[]',        -- [{method, path, description}]
    events JSONB DEFAULT '[]',               -- Emittierte Events

    version VARCHAR(20),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- Feedback-Memory (lernt aus Korrekturen)
CREATE TABLE feedback_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    module_id UUID REFERENCES module_registry(id),

    -- Original
    original_context TEXT,                   -- Worauf bezog sich das Feedback?
    original_response TEXT,                  -- Was war die ursprüngliche LLM-Antwort?

    -- Korrektur
    correction TEXT NOT NULL,                -- Was war falsch / was ist richtig?
    correction_type VARCHAR(50),             -- factual, architectural, performance, security

    -- Für semantische Suche
    context_embedding_key VARCHAR(255),      -- Für schnelle Suche

    -- Relevanz
    times_applied INTEGER DEFAULT 0,         -- Wie oft wurde diese Korrektur angewendet?
    last_applied_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_feedback_memory_module ON feedback_memory(module_id);

-- Session-Memory (Zusammenfassungen abgeschlossener Sessions)
CREATE TABLE session_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) UNIQUE,
    module_id UUID REFERENCES module_registry(id),

    -- Zusammenfassung
    summary TEXT NOT NULL,                   -- LLM-generierte Zusammenfassung
    key_decisions JSONB DEFAULT '[]',        -- Wichtigste Entscheidungen
    lessons_learned JSONB DEFAULT '[]',      -- Was wurde gelernt?

    -- Für zukünftige Sessions
    reusable_patterns JSONB DEFAULT '[]',    -- Wiederverwendbare Muster
    warnings JSONB DEFAULT '[]',             -- Warnungen für zukünftige Entwicklung

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 6.3 Kontext-Service Implementation

```python
# services/context_service.py

class DevelopmentContextService:
    """
    Baut den vollständigen Kontext für LLM-Anfragen auf.
    Nutzt das Memory-System für relevante historische Daten.
    """

    async def build_context(
        self,
        session_id: str,
        iteration_number: int,
        current_question: str | None = None
    ) -> str:
        """
        Baut vollständigen Kontext für die nächste LLM-Anfrage auf.
        """
        context_parts = []

        # 1. Session-Daten laden
        session = await self._get_session(session_id)
        module = await self._get_module(session.module_id)

        # 2. Modul-Architektur
        architecture = await self._get_architecture(session.module_id)
        if architecture:
            context_parts.append(self._format_architecture(architecture))

        # 3. Hochgeladene Dateien mit Erläuterungen
        files = await self._get_session_files(session_id)
        if files:
            context_parts.append(self._format_files(files))

        # 4. Aufgabenbeschreibung
        context_parts.append(f"""
## Aufgabe
{session.task_description}

Kategorie: {session.task_category}
Ziel-Version: {session.base_version} → {session.target_version}
""")

        # 5. Bisherige Iterationen dieser Session
        iterations = await self._get_iterations(session_id, limit=iteration_number)
        if iterations:
            context_parts.append(self._format_iterations(iterations))

        # 6. Relevante Korrekturen aus dem Memory
        if current_question:
            corrections = await self._get_relevant_corrections(
                module_id=session.module_id,
                query=current_question,
                limit=5
            )
            if corrections:
                context_parts.append(self._format_corrections(corrections))

        # 7. Letzte Modul-Änderungen
        recent_changes = await self._get_module_history(session.module_id, limit=5)
        if recent_changes:
            context_parts.append(self._format_history(recent_changes))

        return "\n\n---\n\n".join(context_parts)

    def _format_corrections(self, corrections: list) -> str:
        """Formatiert frühere Korrekturen als Warnung."""
        text = "## ⚠️ Frühere Korrekturen (UNBEDINGT BEACHTEN!)\n\n"
        for c in corrections:
            text += f"- **Kontext:** {c.original_context[:100]}...\n"
            text += f"  **Korrektur:** {c.correction}\n\n"
        return text

    def _format_iterations(self, iterations: list) -> str:
        """Formatiert bisherige Iterationen."""
        text = "## Bisherige Iterationen\n\n"
        for it in iterations:
            text += f"### Iteration {it.iteration_number}\n"
            text += f"**Vorschlag:** {it.proposal_content[:500]}...\n"
            if it.feedback_content:
                text += f"**Feedback:** {it.feedback_content}\n"
            text += "\n"
        return text
```

---

## 7. Phase 5: Freigabe

### 7.1 Freigabe-Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FREIGABE                                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Session: Neue Prüfungslogik für @flowaudit/checklists                          │
│  Status: Iteration #4 - Bereit zur Freigabe                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ FINALER PLAN                                                             │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ ✓ 3 neue Services (RequirementParser, RuleGenerator, ExternalAPIClient) │    │
│  │ ✓ 3 neue API-Endpunkte                                                  │    │
│  │ ✓ 3 neue Datenbank-Tabellen                                             │    │
│  │ ✓ Async-Implementierung für Performance                                 │    │
│  │ ✓ Fehlerbehandlung für XLSX                                             │    │
│  │ ✓ Schweregrade für Findings (info, warning, error)                      │    │
│  │                                                                          │    │
│  │ [Vollständigen Plan anzeigen]                                           │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ CHECKLISTE VOR FREIGABE                                                  │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │ [✓] Ich habe den Implementierungsplan vollständig geprüft              │    │
│  │ [✓] Die Architektur passt zum bestehenden System                        │    │
│  │ [✓] Performance-Anforderungen wurden berücksichtigt                     │    │
│  │ [✓] Sicherheitsaspekte wurden geprüft                                   │    │
│  │ [ ] Ich möchte vor der Entwicklung benachrichtigt werden                │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [← Zurück zum Feedback]              [✓ Entwicklung freigeben]                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Datenmodell: Freigabe

```sql
-- Erweiterung der development_sessions Tabelle
ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    approval_checklist JSONB DEFAULT '{}';   -- {plan_reviewed: true, architecture_ok: true, ...}

ALTER TABLE development_sessions ADD COLUMN IF NOT EXISTS
    final_plan_id UUID REFERENCES development_iterations(id);  -- Verweis auf finale Iteration
```

---

## 8. Phase 6: Entwicklung + Testing (parallel)

### 8.1 Parallele Ausführung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ENTWICKLUNG + TESTING                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Session: Neue Prüfungslogik                     Status: In Entwicklung (67%)  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ ENTWICKLUNG                                          TESTING             │    │
│  ├────────────────────────────────────┬────────────────────────────────────┤    │
│  │                                    │                                     │    │
│  │ ✓ RequirementParser               │ ✓ test_requirement_parser.py       │    │
│  │   └─ services/requirement_parser.py│   └─ 12/12 Tests bestanden        │    │
│  │                                    │                                     │    │
│  │ ✓ RuleGenerator                   │ ✓ test_rule_generator.py           │    │
│  │   └─ services/rule_generator.py   │   └─ 8/8 Tests bestanden           │    │
│  │                                    │                                     │    │
│  │ ◐ ExternalAPIClient               │ ◌ test_external_api.py             │    │
│  │   └─ clients/external_api.py      │   └─ Wartet auf Implementation     │    │
│  │                                    │                                     │    │
│  │ ◌ API-Endpunkte                   │ ◌ test_api_endpoints.py            │    │
│  │   └─ api/checklists_v2.py         │   └─ Wartet auf Implementation     │    │
│  │                                    │                                     │    │
│  │ ◌ Datenbank-Migration             │ ◌ Migration-Test                    │    │
│  │   └─ migrations/007_*.py          │   └─ Wartet auf Migration          │    │
│  │                                    │                                     │    │
│  └────────────────────────────────────┴────────────────────────────────────┘    │
│                                                                                  │
│  Logs: [Development] [Testing] [Errors]                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ > Generating ExternalAPIClient with async httpx...                       │    │
│  │ > Adding rate limiting decorator...                                      │    │
│  │ > Implementing Bearer token authentication...                            │    │
│  │ > _                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [Pause]  [Abbrechen]  [Details anzeigen]                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Datenmodell: Entwicklungs-Tasks

```sql
CREATE TABLE development_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES development_sessions(id) ON DELETE CASCADE,

    -- Task-Definition
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,          -- implementation, test, migration, documentation
    task_order INTEGER NOT NULL,             -- Reihenfolge

    -- Abhängigkeiten
    depends_on JSONB DEFAULT '[]',           -- Array von task_ids

    -- Ziel-Dateien
    target_files JSONB DEFAULT '[]',         -- [{path, action: "create"|"modify"}]

    -- Status
    status VARCHAR(20) DEFAULT 'pending',    -- pending, in_progress, completed, failed, skipped
    progress INTEGER DEFAULT 0,              -- 0-100

    -- Ergebnis
    output_files JSONB DEFAULT '[]',         -- Generierte Dateien
    output_log TEXT,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- LLM-Nutzung
    llm_tokens_used INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dev_tasks_session ON development_tasks(session_id, task_order);

-- Test-Ergebnisse
CREATE TABLE development_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES development_tasks(id) ON DELETE CASCADE,

    test_file VARCHAR(500),
    test_name VARCHAR(255),

    status VARCHAR(20),                      -- passed, failed, skipped, error
    duration_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. API-Endpunkte

### 9.1 Development Session API

```
# Module Registry
GET  /api/v1/modules                         → Liste aller Module
GET  /api/v1/modules/{id}                    → Modul-Details
GET  /api/v1/modules/{id}/architecture       → Modul-Architektur
GET  /api/v1/modules/workflow-diagram        → Flussdiagramm-Daten

# Development Sessions
POST /api/v1/development/sessions            → Neue Session starten
GET  /api/v1/development/sessions            → Alle Sessions
GET  /api/v1/development/sessions/{id}       → Session-Details
PUT  /api/v1/development/sessions/{id}       → Session aktualisieren

# Dateien
POST /api/v1/development/sessions/{id}/files → Datei hochladen
GET  /api/v1/development/sessions/{id}/files → Alle Dateien
PUT  /api/v1/development/sessions/{id}/files/{file_id} → Erläuterung ändern

# Iterationen / Feedback-Loop
POST /api/v1/development/sessions/{id}/analyze        → LLM-Analyse starten
GET  /api/v1/development/sessions/{id}/iterations     → Alle Iterationen
POST /api/v1/development/sessions/{id}/iterations/{n}/feedback → Feedback geben

# Freigabe
POST /api/v1/development/sessions/{id}/approve        → Entwicklung freigeben

# Entwicklung
POST /api/v1/development/sessions/{id}/start-development → Entwicklung starten
GET  /api/v1/development/sessions/{id}/tasks          → Task-Status
GET  /api/v1/development/sessions/{id}/tasks/{task_id}/logs → Task-Logs

# Memory
GET  /api/v1/development/memory/corrections           → Gespeicherte Korrekturen
GET  /api/v1/development/memory/sessions/{module_id}  → Session-Zusammenfassungen
```

---

## 10. Zusammenfassung

### 10.1 Der komplette Workflow

```
1. MODUL AUSWÄHLEN
   ├─ Bestehendes Modul → Version erhöhen
   └─ Neues Modul → Im Flussdiagramm positionieren

2. DATEIEN HOCHLADEN
   └─ Pro Datei: Erläuterung eingeben (Pflicht)

3. AUFGABE BESCHREIBEN
   └─ Was soll entwickelt werden?

4. ITERATIVER FEEDBACK-LOOP
   ┌─────────────────────────────────┐
   │ LLM analysiert + macht Vorschlag│
   │              ↓                  │
   │ User gibt Feedback              │
   │              ↓                  │
   │ LLM überarbeitet                │
   │              ↓                  │
   │ Wiederholen bis zufrieden       │
   └─────────────────────────────────┘

5. FREIGABE
   └─ User gibt Entwicklung frei

6. ENTWICKLUNG + TESTING
   └─ Parallel: Code generieren + Tests ausführen

7. ABSCHLUSS
   ├─ Memory aktualisieren (Learnings speichern)
   └─ Neue Modul-Version registrieren
```

### 10.2 Memory-Formel

```
MEMORY = Architektur + Dateien + Iterationen + Korrekturen + History

Bei jeder LLM-Anfrage:
- Architektur des Moduls laden
- Hochgeladene Dateien + Erläuterungen einbinden
- Bisherige Iterationen dieser Session
- Relevante Korrekturen aus früheren Sessions
- Letzte Änderungen am Modul
```

### 10.3 Implementierungs-Prioritäten

| Phase | Komponente | Aufwand | Wert |
|-------|------------|---------|------|
| **1** | Module Registry + Workflow-Diagram | 3 Tage | Hoch |
| **1** | Development Session + Datei-Upload | 3 Tage | Kritisch |
| **2** | Iterativer Feedback-Loop | 4 Tage | Kritisch |
| **2** | Context-Service (Memory) | 3 Tage | Kritisch |
| **3** | Freigabe-Workflow | 2 Tage | Mittel |
| **3** | Development + Testing Pipeline | 5 Tage | Hoch |
| **4** | Memory-Persistenz + Learnings | 3 Tage | Hoch |

---

## 11. Multi-LLM-Strategie (GLM + Anthropic)

### 11.1 Warum zwei LLMs?

| LLM | Stärken | Einsatz im Development-Modul |
|-----|---------|------------------------------|
| **GLM-4** | Schnell, günstig, gute Code-Analyse | Erste Analyse, Strukturierung, Validierung |
| **Anthropic Claude** | Präzise, kreativ, tiefes Verständnis | Detaillierte Vorschläge, Code-Generierung, Feedback-Verarbeitung |

### 11.2 Kombinationsmuster

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-LLM WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 1: PIPELINE (Sequentiell)                                           │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │  Dateien + Aufgabe                                                         │ │
│  │         │                                                                   │ │
│  │         ▼                                                                   │ │
│  │  ┌──────────────┐     ┌──────────────────────────────────┐                 │ │
│  │  │   GLM-4      │────>│        ANTHROPIC CLAUDE          │                 │ │
│  │  │              │     │                                  │                 │ │
│  │  │ • Dateien    │     │ • Nimmt GLM-Analyse als Input    │                 │ │
│  │  │   parsen     │     │ • Erstellt detaillierten Plan    │                 │ │
│  │  │ • Struktur   │     │ • Generiert Code                 │                 │ │
│  │  │   erkennen   │     │ • Verarbeitet Feedback           │                 │ │
│  │  │ • Zusammen-  │     │                                  │                 │ │
│  │  │   fassung    │     │                                  │                 │ │
│  │  └──────────────┘     └──────────────────────────────────┘                 │ │
│  │       (schnell,              (präzise, kreativ)                            │ │
│  │        günstig)                                                            │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 2: PARALLEL (Vergleich)                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │              Aufgabe                                                        │ │
│  │                │                                                            │ │
│  │         ┌──────┴──────┐                                                     │ │
│  │         ▼             ▼                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐                                        │ │
│  │  │   GLM-4      │  │   ANTHROPIC  │                                        │ │
│  │  │   Vorschlag  │  │   Vorschlag  │                                        │ │
│  │  └──────────────┘  └──────────────┘                                        │ │
│  │         │                 │                                                 │ │
│  │         └────────┬────────┘                                                 │ │
│  │                  ▼                                                          │ │
│  │         ┌──────────────┐                                                   │ │
│  │         │  VERGLEICH   │  → User wählt besseren Vorschlag                  │ │
│  │         │  + MERGE     │  → Oder: Kombinierter Vorschlag                   │ │
│  │         └──────────────┘                                                   │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ MUSTER 3: SPEZIALISIERT (Task-basiert)                                     │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                             │ │
│  │  Task                         LLM                                          │ │
│  │  ────                         ───                                          │ │
│  │  Datei-Analyse                GLM-4        (schnell, strukturiert)         │ │
│  │  Code-Validierung             GLM-4        (regelbasiert)                  │ │
│  │  Implementierungsplan         ANTHROPIC    (kreativ, detailliert)          │ │
│  │  Code-Generierung             ANTHROPIC    (präzise, best practices)       │ │
│  │  Feedback-Verarbeitung        ANTHROPIC    (Verständnis, Nuancen)          │ │
│  │  Test-Generierung             ANTHROPIC    (Edge Cases, Coverage)          │ │
│  │  Dokumentation                GLM-4        (strukturiert, schnell)         │ │
│  │                                                                             │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Implementierung: Multi-LLM Service

```python
# services/multi_llm_service.py

from enum import Enum
from typing import AsyncIterator

class LLMRole(str, Enum):
    """Rollen für verschiedene LLM-Tasks."""
    ANALYZER = "analyzer"           # Schnelle Analyse, Strukturierung
    PLANNER = "planner"             # Detaillierte Planung
    CODER = "coder"                 # Code-Generierung
    REVIEWER = "reviewer"           # Code-Review, Validierung
    FEEDBACK_PROCESSOR = "feedback" # Feedback verarbeiten

class LLMConfig:
    """Konfiguration welches LLM für welche Rolle."""

    DEFAULT_ROUTING = {
        LLMRole.ANALYZER: "glm-4",
        LLMRole.PLANNER: "claude-3-opus",
        LLMRole.CODER: "claude-3-opus",
        LLMRole.REVIEWER: "glm-4",
        LLMRole.FEEDBACK_PROCESSOR: "claude-3-opus",
    }


class MultiLLMService:
    """
    Orchestriert mehrere LLMs für verschiedene Aufgaben.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.glm_client = GLMClient()
        self.anthropic_client = AnthropicClient()
        self.routing = LLMConfig.DEFAULT_ROUTING.copy()

    async def execute_pipeline(
        self,
        session_id: str,
        files: list[DevelopmentFile],
        task_description: str,
        context: str,
    ) -> PipelineResult:
        """
        Führt die GLM → Anthropic Pipeline aus.

        1. GLM-4: Schnelle Voranalyse
        2. Anthropic: Detaillierter Vorschlag basierend auf GLM-Analyse
        """
        # Phase 1: GLM-4 Analyse
        glm_analysis = await self._analyze_with_glm(files, task_description)

        # Phase 2: Anthropic Vorschlag mit GLM-Kontext
        enriched_context = f"""
{context}

## Voranalyse (GLM-4)
{glm_analysis.summary}

### Erkannte Struktur
{glm_analysis.structure}

### Identifizierte Komponenten
{glm_analysis.components}

### Mögliche Herausforderungen
{glm_analysis.challenges}
"""

        anthropic_proposal = await self._create_proposal_with_anthropic(
            enriched_context,
            task_description
        )

        return PipelineResult(
            glm_analysis=glm_analysis,
            proposal=anthropic_proposal,
            total_tokens={
                "glm": glm_analysis.tokens_used,
                "anthropic": anthropic_proposal.tokens_used,
            }
        )

    async def execute_parallel(
        self,
        context: str,
        task_description: str,
    ) -> ParallelResult:
        """
        Führt beide LLMs parallel aus und vergleicht Ergebnisse.
        """
        # Parallel ausführen
        glm_task = asyncio.create_task(
            self._create_proposal_with_glm(context, task_description)
        )
        anthropic_task = asyncio.create_task(
            self._create_proposal_with_anthropic(context, task_description)
        )

        glm_result, anthropic_result = await asyncio.gather(
            glm_task, anthropic_task
        )

        # Ergebnisse vergleichen und Unterschiede hervorheben
        comparison = self._compare_proposals(glm_result, anthropic_result)

        return ParallelResult(
            glm_proposal=glm_result,
            anthropic_proposal=anthropic_result,
            comparison=comparison,
        )

    async def process_feedback(
        self,
        iteration: DevelopmentIteration,
        feedback: str,
    ) -> str:
        """
        Verarbeitet User-Feedback immer mit Anthropic.
        (Besseres Verständnis von Nuancen und Kritik)
        """
        return await self.anthropic_client.complete(
            messages=[
                {"role": "system", "content": FEEDBACK_SYSTEM_PROMPT},
                {"role": "user", "content": f"""
Vorheriger Vorschlag:
{iteration.proposal_content}

User-Feedback:
{feedback}

Bitte überarbeite den Vorschlag basierend auf dem Feedback.
"""}
            ],
            temperature=0.7,
        )

    async def _analyze_with_glm(
        self,
        files: list[DevelopmentFile],
        task: str,
    ) -> GLMAnalysis:
        """Schnelle Strukturanalyse mit GLM-4."""
        file_contents = "\n\n".join([
            f"### {f.original_filename}\n{f.parsed_content}\n\nErläuterung: {f.user_annotation}"
            for f in files
        ])

        response = await self.glm_client.complete(
            messages=[
                {"role": "system", "content": GLM_ANALYZER_PROMPT},
                {"role": "user", "content": f"""
Analysiere folgende Dateien für die Aufgabe: {task}

{file_contents}
"""}
            ],
            temperature=0.3,  # Niedriger für konsistente Analyse
        )

        return GLMAnalysis.parse(response)
```

### 11.4 Datenmodell: Multi-LLM Tracking

```sql
-- Erweiterung der development_iterations Tabelle
ALTER TABLE development_iterations ADD COLUMN IF NOT EXISTS
    llm_chain JSONB DEFAULT '[]';
    -- Speichert die Kette der LLM-Aufrufe:
    -- [
    --   {provider: "glm", model: "glm-4", role: "analyzer", tokens: 1200, latency_ms: 450},
    --   {provider: "anthropic", model: "claude-3-opus", role: "planner", tokens: 3500, latency_ms: 2100}
    -- ]

-- LLM-Routing-Konfiguration pro Tenant
CREATE TABLE llm_routing_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),

    -- Routing-Regeln
    routing_mode VARCHAR(20) DEFAULT 'pipeline',  -- pipeline, parallel, specialized
    role_assignments JSONB DEFAULT '{}',
    -- {
    --   "analyzer": {"provider": "glm", "model": "glm-4"},
    --   "planner": {"provider": "anthropic", "model": "claude-3-opus"},
    --   "coder": {"provider": "anthropic", "model": "claude-3-opus"},
    --   ...
    -- }

    -- Fallback
    fallback_provider VARCHAR(50) DEFAULT 'anthropic',
    fallback_model VARCHAR(100) DEFAULT 'claude-3-sonnet',

    -- Kosten-Limits
    max_tokens_per_iteration INTEGER DEFAULT 50000,
    prefer_cheaper BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 11.5 Kosten-Optimierung

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KOSTEN-ÜBERSICHT                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Typische Session mit 5 Iterationen:                                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ OHNE Multi-LLM (nur Anthropic)                                          │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │ 5 × Analyse + Vorschlag: ~25.000 Tokens × $15/1M = $0.375               │    │
│  │ 5 × Feedback-Verarbeitung: ~15.000 Tokens × $15/1M = $0.225             │    │
│  │ Code-Generierung: ~30.000 Tokens × $15/1M = $0.450                      │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ GESAMT: ~$1.05 pro Session                                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ MIT Multi-LLM (GLM + Anthropic)                                         │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │ 5 × GLM-4 Voranalyse: ~10.000 Tokens × $1/1M = $0.01                    │    │
│  │ 5 × Anthropic Vorschlag: ~15.000 Tokens × $15/1M = $0.225               │    │
│  │ 5 × Anthropic Feedback: ~15.000 Tokens × $15/1M = $0.225                │    │
│  │ Code-Generierung: ~30.000 Tokens × $15/1M = $0.450                      │    │
│  │ ─────────────────────────────────────────────────────────────           │    │
│  │ GESAMT: ~$0.91 pro Session (-13%)                                       │    │
│  │                                                                          │    │
│  │ + Bonus: GLM-Analyse ist 3x schneller → Bessere UX                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 11.6 UI: LLM-Auswahl und Transparenz

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         LLM-STATUS                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Iteration #3                                                                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ LLM-Kette                                                               │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  1. ✓ GLM-4 (Voranalyse)         1.200 Tokens    0.45s    $0.001        │    │
│  │     └─ Struktur erkannt, 3 Komponenten identifiziert                    │    │
│  │                                                                          │    │
│  │  2. ✓ Claude Opus (Vorschlag)    3.500 Tokens    2.1s     $0.053        │    │
│  │     └─ Detaillierter Implementierungsplan erstellt                      │    │
│  │                                                                          │    │
│  │  Gesamt: 4.700 Tokens | 2.55s | $0.054                                  │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  [LLM-Einstellungen ändern]                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Erweiterungen für die Zukunft

1. **Semantische Suche im Memory** - pgvector für bessere Korrektur-Findung
2. **Auto-Dokumentation** - Generierung von CHANGELOG und Docs
3. **Multi-User Kollaboration** - Mehrere User an einer Session
4. **A/B-Testing** - Verschiedene Implementierungen vergleichen
5. **Rollback** - Auf frühere Versionen zurückrollen
6. **Weitere LLMs** - Mistral, Llama, DeepSeek als zusätzliche Optionen
7. **Adaptive Routing** - Automatische LLM-Auswahl basierend auf Task-Komplexität
