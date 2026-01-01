# Implementierungsaufgaben

## Übersicht der nächsten Features

| Feature | Priorität | Geschätzter Aufwand |
|---------|-----------|---------------------|
| Modul-Distribution-System | Hoch | 2 Wochen |
| Admin-Dashboard | Mittel | 2 Wochen |
| Deployment-Packaging | Mittel | 1 Woche |
| Workflow-Historisierung | Hoch | 1.5 Wochen |

---

## 1. Modul-Distribution-System

### Ziel
Module als installierbare Pakete verteilen, sodass Kunden auf eigenen Servern Module installieren/updaten können.

### Aufgaben

#### 1.1 Modul-Manifest erstellen
```
Datei: modules/vp_ai/module.json
```
- [ ] JSON-Schema für module.json definieren
- [ ] VP-AI Modul als erstes Beispiel refactoren
- [ ] Abhängigkeiten, Version, Features dokumentieren

#### 1.2 ModuleManager implementieren
```
Datei: backend/app/core/module_manager.py
```
- [ ] `list_installed()` - Installierte Module auflisten
- [ ] `get_available()` - Verfügbare Module von Registry laden
- [ ] `install_module(id, version)` - Modul installieren
- [ ] `update_module(id)` - Modul aktualisieren
- [ ] `uninstall_module(id)` - Modul entfernen
- [ ] `get_module_config(id)` - Konfiguration lesen
- [ ] `set_module_config(id, config)` - Konfiguration speichern

#### 1.3 Modul-API-Endpoints
```
Datei: backend/app/api/modules.py
```
- [ ] `GET /api/v1/modules/installed`
- [ ] `GET /api/v1/modules/available`
- [ ] `POST /api/v1/modules/{id}/install`
- [ ] `POST /api/v1/modules/{id}/update`
- [ ] `DELETE /api/v1/modules/{id}`
- [ ] `GET /api/v1/modules/{id}/config`
- [ ] `PUT /api/v1/modules/{id}/config`

#### 1.4 Paket-Format (.adbpkg)
- [ ] Struktur definieren (ZIP mit Manifest)
- [ ] Build-Script für Paket-Erstellung
- [ ] Signatur/Checksum für Integrität

#### 1.5 Datenbank-Schema
```sql
CREATE TABLE modules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'installed',
    config_json JSONB,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 2. Admin-Dashboard

### Ziel
Übersicht über System-Status, Module, Prozesse, Roadmap und Flussdiagramme.

### Aufgaben

#### 2.1 Backend-Modelle
```
Datei: backend/app/models/system_status.py
```
- [ ] `SystemProcess` - Laufende/abgeschlossene Prozesse
- [ ] `DevelopmentItem` - Features, Bugs, Verbesserungen

#### 2.2 Dashboard-API
```
Datei: backend/app/api/dashboard.py
```
- [ ] `GET /api/v1/dashboard/overview` - Gesamt-Übersicht
- [ ] `GET /api/v1/dashboard/processes` - Prozess-Liste
- [ ] `GET /api/v1/dashboard/processes/{id}` - Prozess-Details
- [ ] `POST /api/v1/dashboard/processes/{id}/cancel`
- [ ] `GET /api/v1/dashboard/development` - Entwicklungs-Items
- [ ] `POST /api/v1/dashboard/development` - Neues Item
- [ ] `GET /api/v1/dashboard/roadmap` - Roadmap

#### 2.3 Flowchart-API
```
Datei: backend/app/api/flowchart.py
```
- [ ] `GET /api/v1/flowchart/modules` - Modul-Abhängigkeiten
- [ ] `GET /api/v1/flowchart/data-flow` - Datenfluss-Diagramm

#### 2.4 Frontend-Dashboard
```
Verzeichnis: frontend/src/views/admin/
```
- [ ] `Dashboard.vue` - Hauptseite
- [ ] `StatusCard.vue` - Status-Karten
- [ ] `ModulesPanel.vue` - Modul-Übersicht
- [ ] `ProcessesPanel.vue` - Prozess-Liste
- [ ] `DevelopmentPanel.vue` - Roadmap/TODOs
- [ ] `FlowchartPanel.vue` - Flussdiagramm (vue-flow oder ähnlich)

#### 2.5 Datenbank-Schema
```sql
CREATE TABLE system_processes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    progress_percent INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    error_message TEXT,
    metadata_json JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE development_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(50),  -- feature, bug, improvement
    status VARCHAR(50), -- planned, in_progress, testing, done
    priority VARCHAR(20),
    module_id VARCHAR(50) REFERENCES modules(id),
    target_version VARCHAR(20),
    assignee VARCHAR(100),
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 3. Deployment-Packaging

### Ziel
Kundenspezifische Installationspakete erstellen, die einfach deployed werden können.

### Aufgaben

#### 3.1 Kunden-Konfigurations-Schema
```
Datei: deployment/customer_config.yaml
```
- [ ] YAML-Schema definieren
- [ ] Beispiel-Konfiguration erstellen
- [ ] Validierung implementieren

#### 3.2 Deployment-Generator
```
Datei: tools/deployment_generator.py
```
- [ ] `DeploymentGenerator` Klasse
- [ ] Docker-Images exportieren
- [ ] docker-compose.yml generieren
- [ ] .env.template generieren
- [ ] Branding anwenden
- [ ] Module einpacken
- [ ] Dokumentation generieren
- [ ] ZIP-Archiv erstellen

#### 3.3 Installations-Scripts
```
Verzeichnis: deployment/scripts/
```
- [ ] `setup.sh` - Erstinstallation
- [ ] `upgrade.sh` - Update auf neue Version
- [ ] `backup.sh` - Datenbank + Dateien sichern
- [ ] `restore.sh` - Backup wiederherstellen

#### 3.4 Datenbank-Schema
```sql
CREATE TABLE deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL,
    customer_name VARCHAR(200),
    config_json JSONB,
    version VARCHAR(20),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    notes TEXT
);
```

---

## 4. Workflow-Historisierung (LLM-Kontext)

### Ziel
Vollständige Historisierung des Entwicklungs-Workflows, sodass:
1. Die Entwicklung eines Moduls von der Benennung bis zum Deployment nachvollziehbar ist
2. Die LLM bei jedem Aufruf genug Kontext hat (vorherige Entscheidungen, Feedback-Schleifen)
3. Datei-Uploads und deren Verarbeitung dokumentiert werden
4. **Architektur-Entscheidungen und Strukturen persistent gespeichert werden**

### Aufgaben

#### 4.1 Modul-Entwicklungs-History
```
Datei: backend/app/models/module_history.py
```
- [ ] `ModuleEvent` - Einzelnes Event in der Modul-Geschichte
- [ ] Event-Typen: `created`, `renamed`, `file_added`, `file_updated`, `config_changed`, `llm_feedback`, `deployed`
- [ ] Speichern wer, wann, was geändert hat

#### 4.2 Architektur-Speicherung (NEU)
```
Datei: backend/app/models/module_architecture.py
```
- [ ] `ModuleArchitecture` - Architektur-Dokument für ein Modul
- [ ] `ArchitectureComponent` - Einzelne Komponenten (Services, Models, APIs)
- [ ] `ArchitectureDecision` - ADRs (Architecture Decision Records)
- [ ] `ComponentRelation` - Beziehungen zwischen Komponenten (depends_on, uses, extends)

**Zu speichern:**
| Kategorie | Inhalte |
|-----------|---------|
| **Struktur** | Verzeichnisbaum, Dateien, Module |
| **Komponenten** | Services, Models, APIs, Utils |
| **Beziehungen** | Dependencies, Imports, Datenfluss |
| **Entscheidungen** | Warum wurde X so implementiert? Alternativen? |
| **Patterns** | Verwendete Design-Patterns (Repository, Factory, etc.) |
| **Schnittstellen** | API-Endpunkte, Events, Webhooks |

#### 4.3 LLM-Feedback-Historisierung
```
Datei: backend/app/models/llm_history.py
```
- [ ] `LLMConversation` - Konversations-Session
- [ ] `LLMMessage` - Einzelne Nachricht (User/Assistant)
- [ ] `LLMFeedback` - Bewertung/Korrektur durch User
- [ ] Kontext-Verkettung: Jede neue Anfrage kann vorherige Konversationen referenzieren

#### 4.4 Datei-Upload-Tracking
```
Datei: backend/app/models/file_history.py
```
- [ ] `FileUpload` - Hochgeladene Datei mit Metadaten
- [ ] `FileVersion` - Versionen einer Datei
- [ ] `FileProcessingLog` - Was wurde mit der Datei gemacht (Parsing, Embedding, etc.)

#### 4.5 Kontext-Service für LLM
```
Datei: backend/app/services/context_service.py
```
- [ ] `get_module_context(module_id)` - Vollständige Geschichte eines Moduls
- [ ] `get_conversation_context(session_id, limit)` - Letzte N Nachrichten
- [ ] `get_relevant_history(query)` - Semantische Suche in History
- [ ] `build_llm_prompt_with_context(question, module_id)` - Prompt mit vollem Kontext

#### 4.6 API-Endpoints
```
Datei: backend/app/api/history.py + backend/app/api/architecture.py
```
- [ ] `GET /api/v1/modules/{id}/history` - Modul-Timeline
- [ ] `GET /api/v1/conversations` - Alle Konversationen
- [ ] `GET /api/v1/conversations/{id}` - Eine Konversation
- [ ] `POST /api/v1/conversations/{id}/feedback` - Feedback speichern
- [ ] `GET /api/v1/files/{id}/history` - Datei-Versionen
- [ ] `GET /api/v1/modules/{id}/architecture` - Modul-Architektur
- [ ] `PUT /api/v1/modules/{id}/architecture` - Architektur aktualisieren
- [ ] `GET /api/v1/modules/{id}/components` - Komponenten-Liste
- [ ] `POST /api/v1/modules/{id}/decisions` - ADR hinzufügen
- [ ] `GET /api/v1/modules/{id}/relations` - Komponenten-Beziehungen

#### 4.7 Datenbank-Schema
```sql
-- Modul-Events für vollständige Nachvollziehbarkeit
CREATE TABLE module_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,  -- Details je nach Event-Typ
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Timeline-Abfragen
CREATE INDEX idx_module_events_module_time ON module_events(module_id, created_at DESC);

-- LLM-Konversationen
CREATE TABLE llm_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    session_name VARCHAR(200),
    context_summary TEXT,  -- Zusammenfassung für LLM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Einzelne Nachrichten in Konversation
CREATE TABLE llm_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES llm_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Feedback zu LLM-Antworten
CREATE TABLE llm_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES llm_messages(id) ON DELETE CASCADE,
    rating INTEGER,  -- 1-5 oder thumbs up/down
    correction TEXT,  -- Was war falsch / bessere Antwort
    tags JSONB,  -- z.B. ["hallucination", "incomplete", "wrong_source"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datei-Uploads mit Versionen
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    original_filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),
    uploaded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_uploads(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_uploads(id) ON DELETE CASCADE,
    process_type VARCHAR(50),  -- 'parse', 'embed', 'chunk', 'ocr'
    status VARCHAR(20),
    result_summary JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- =====================================================
-- ARCHITEKTUR-SPEICHERUNG
-- =====================================================

-- Modul-Architektur (Hauptdokument)
CREATE TABLE module_architecture (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id) UNIQUE,
    description TEXT,  -- Übersicht der Architektur
    directory_structure JSONB,  -- Verzeichnisbaum als JSON
    tech_stack JSONB,  -- {backend: ["FastAPI", "SQLAlchemy"], frontend: ["Vue3"]}
    patterns JSONB,  -- ["Repository", "Factory", "Service Layer"]
    version VARCHAR(20),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Einzelne Komponenten
CREATE TABLE architecture_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'service', 'model', 'api', 'util', 'config'
    file_path VARCHAR(500),
    description TEXT,
    responsibilities JSONB,  -- ["Datenvalidierung", "API-Aufrufe"]
    public_interface JSONB,  -- {methods: [...], properties: [...]}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_arch_components_module ON architecture_components(module_id);

-- Beziehungen zwischen Komponenten
CREATE TABLE component_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_component_id UUID REFERENCES architecture_components(id) ON DELETE CASCADE,
    target_component_id UUID REFERENCES architecture_components(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,  -- 'depends_on', 'uses', 'extends', 'implements'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_component_id, target_component_id, relation_type)
);

-- Architecture Decision Records (ADRs)
CREATE TABLE architecture_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'accepted',  -- 'proposed', 'accepted', 'deprecated', 'superseded'
    context TEXT,  -- Warum wurde die Entscheidung getroffen?
    decision TEXT,  -- Was wurde entschieden?
    alternatives JSONB,  -- [{name: "...", pros: [...], cons: [...]}]
    consequences TEXT,  -- Auswirkungen der Entscheidung
    related_components JSONB,  -- [component_id, ...]
    superseded_by UUID REFERENCES architecture_decisions(id),
    decided_by VARCHAR(100),
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_arch_decisions_module ON architecture_decisions(module_id);
```

### Workflow-Beispiel

```
1. Modul erstellen
   └─> Event: module_created {name: "Vergabeprüfung", description: "..."}
   └─> Architecture: Initiale Struktur anlegen

2. Architektur definieren
   └─> Components: RAGService, ChecklistAnalyzer, DocumentParser
   └─> Relations: ChecklistAnalyzer --uses--> RAGService
   └─> ADR: "Warum RAG statt Fine-Tuning?" mit Alternativen

3. Dateien hochladen
   └─> Event: file_added {filename: "vergabe_checkliste.xlsx", size: 12400}
   └─> FileProcessingLog: parse, embed, chunk

4. Konfiguration anpassen
   └─> Event: config_changed {old: {...}, new: {...}}

5. LLM-Interaktion starten
   └─> Conversation erstellen
   └─> Messages: User fragt, LLM antwortet
   └─> Feedback: User korrigiert Antwort
   └─> Nächste Anfrage hat Korrektur + Architektur als Kontext!

6. Modul deployen
   └─> Event: deployed {customer: "Kunde X", version: "1.2.0"}
   └─> Architecture: Version 1.2.0 snapshot
```

### Kontext-Aufbau für LLM-Anfragen

```python
def build_llm_context(module_id: str, question: str) -> str:
    """
    Baut vollständigen Kontext für LLM-Anfrage auf.
    Enthält jetzt auch Architektur-Informationen!
    """
    context_parts = []

    # 1. Modul-Metadaten
    module = get_module(module_id)
    context_parts.append(f"## Modul: {module.name}\n{module.description}")

    # 2. ARCHITEKTUR (NEU!)
    architecture = get_module_architecture(module_id)
    if architecture:
        context_parts.append("## Architektur:")
        context_parts.append(f"Tech-Stack: {architecture.tech_stack}")
        context_parts.append(f"Patterns: {architecture.patterns}")

        # Komponenten
        components = get_architecture_components(module_id)
        if components:
            context_parts.append("### Komponenten:")
            for c in components:
                context_parts.append(f"- {c.name} ({c.type}): {c.description}")

        # Relevante ADRs
        decisions = get_relevant_decisions(module_id, question)
        if decisions:
            context_parts.append("### Architektur-Entscheidungen:")
            for d in decisions:
                context_parts.append(f"- {d.title}: {d.decision}")

    # 3. Relevante Events (letzte Änderungen)
    events = get_recent_events(module_id, limit=10)
    if events:
        context_parts.append("## Letzte Änderungen:")
        for e in events:
            context_parts.append(f"- {e.created_at}: {e.event_type}")

    # 4. Vorherige Korrekturen/Feedback (WICHTIG!)
    feedback = get_relevant_feedback(module_id, question)
    if feedback:
        context_parts.append("## Frühere Korrekturen (beachten!):")
        for f in feedback:
            context_parts.append(f"- Ursprüngliche Antwort war falsch: {f.correction}")

    # 5. Letzte Konversation (falls vorhanden)
    last_conv = get_last_conversation(module_id)
    if last_conv:
        context_parts.append(f"## Vorherige Konversation:\n{last_conv.context_summary}")

    return "\n\n".join(context_parts)
```

---

## Befehl zum Starten

Um mit der Implementierung zu beginnen, verwende folgenden Prompt:

```
Implementiere das Modul-Distribution-System basierend auf dem Plan in
docs/PLAN_DISTRIBUTION_DASHBOARD_DEPLOYMENT.md.

Beginne mit:
1. Modul-Manifest-Schema (module.json)
2. ModuleManager-Klasse
3. API-Endpoints für Modul-Verwaltung

Refactore VP-AI als erstes Modul.
```
