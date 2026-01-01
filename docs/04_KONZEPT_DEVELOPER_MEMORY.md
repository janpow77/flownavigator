# Konzept: Developer-Tool mit LLM-Memory

## Übersicht

Ein Developer-Tool, das die komplette Entwicklungshistorie eines Moduls speichert und der LLM als Kontext bereitstellt. Dadurch "erinnert" sich die LLM an alle Entscheidungen, Korrekturen und die Architektur.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MEMORY = DB + RETRIEVAL + PROMPT                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────────┐   │
│   │  DATENBANK  │───>│  RETRIEVAL   │───>│      PROMPT-AUFBAU          │   │
│   │             │    │              │    │                             │   │
│   │ • Events    │    │ • Letzte N   │    │ "Du hast Kontext zu:        │   │
│   │ • Architektur│   │ • Semantisch │    │  - Architektur              │   │
│   │ • Feedback  │    │ • Gewichtet  │    │  - Korrekturen              │   │
│   │ • Dateien   │    │              │    │  - Vorherige Gespräche"     │   │
│   └─────────────┘    └──────────────┘    └─────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Kernprinzip

**Problem:** LLMs haben kein Gedächtnis zwischen Sessions. Jede Anfrage startet bei Null.

**Lösung:** Alles persistent speichern und bei jeder Anfrage relevanten Kontext laden.

```
Session 1: User fragt → LLM antwortet falsch → User korrigiert
                                                      ↓
                                              Korrektur gespeichert
                                                      ↓
Session 2: User fragt ähnlich → LLM bekommt Korrektur als Kontext → Antwortet richtig
```

---

## Was wird gespeichert?

### 1. Modul-Events (Timeline)

Jede Änderung am Modul wird als Event erfasst:

| Event-Typ | Beschreibung | Beispiel-Daten |
|-----------|--------------|----------------|
| `created` | Modul erstellt | `{name: "Vergabeprüfung"}` |
| `renamed` | Modul umbenannt | `{old: "VP", new: "Vergabeprüfung"}` |
| `file_added` | Datei hochgeladen | `{filename: "checkliste.xlsx", size: 12400}` |
| `file_updated` | Datei aktualisiert | `{filename: "checkliste.xlsx", version: 2}` |
| `config_changed` | Konfiguration geändert | `{key: "llm_provider", old: "openai", new: "anthropic"}` |
| `llm_feedback` | LLM-Antwort korrigiert | `{rating: -1, correction: "..."}` |
| `deployed` | Modul deployed | `{customer: "Kunde X", version: "1.2.0"}` |

```sql
CREATE TABLE module_events (
    id UUID PRIMARY KEY,
    module_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Architektur

Struktur und Design-Entscheidungen des Moduls:

```
ModuleArchitecture
├── description: "RAG-basierte Checklisten-Analyse"
├── tech_stack: {backend: ["FastAPI"], frontend: ["Vue3"]}
├── patterns: ["Service Layer", "Repository"]
│
├── Components
│   ├── RAGService (service) - "Retrieval Augmented Generation"
│   ├── ChecklistAnalyzer (service) - "Analysiert Prüfungschecklisten"
│   └── DocumentParser (util) - "Parst PDF/Word/Excel"
│
├── Relations
│   ├── ChecklistAnalyzer --uses--> RAGService
│   └── ChecklistAnalyzer --uses--> DocumentParser
│
└── Decisions (ADRs)
    ├── "Warum RAG statt Fine-Tuning?"
    │   ├── Kontext: "Domäne ändert sich häufig"
    │   ├── Entscheidung: "RAG mit ChromaDB"
    │   └── Alternativen: [{name: "Fine-Tuning", cons: ["Teuer", "Veraltet schnell"]}]
    │
    └── "Warum Vue3 statt React?"
        └── ...
```

### 3. LLM-Konversationen & Feedback

Alle Interaktionen mit der LLM werden gespeichert:

```
LLMConversation (Session)
├── module_id: "vergabepruefung"
├── session_name: "Checklisten-Analyse implementieren"
├── context_summary: "Zusammenfassung für zukünftige Anfragen"
│
└── Messages
    ├── [User] "Wie analysiere ich eine Checkliste?"
    ├── [Assistant] "Du kannst die ChecklistAnalyzer-Klasse..."
    │   └── Feedback: {rating: -1, correction: "Falsch! Es gibt keinen Parser für XLSX"}
    └── [User] "Ok, wie füge ich XLSX-Support hinzu?"
```

**Kritisch:** Das Feedback wird bei zukünftigen Anfragen eingebunden!

### 4. Datei-Uploads

Alle hochgeladenen Dateien mit Versionen und Verarbeitungs-Log:

```
FileUpload
├── original_filename: "vergabe_checkliste.xlsx"
├── mime_type: "application/vnd.openxmlformats..."
├── checksum_sha256: "abc123..."
│
├── Versions
│   ├── v1: "2024-01-15"
│   └── v2: "2024-02-01" (change: "Neue Spalte hinzugefügt")
│
└── ProcessingLog
    ├── parse: completed (chunks: 42)
    ├── embed: completed (vectors: 42)
    └── validate: completed
```

---

## Retrieval-Strategien

### Strategie 1: Letzte N (Einfach)

```python
def get_recent_context(module_id: str, limit: int = 20) -> str:
    events = get_recent_events(module_id, limit=10)
    feedback = get_recent_feedback(module_id, limit=5)
    messages = get_recent_messages(module_id, limit=5)
    return format_context(events, feedback, messages)
```

**Pro:** Schnell, einfach
**Contra:** Findet nicht semantisch ähnliche Einträge

### Strategie 2: Semantische Suche (Erweitert)

```python
def get_relevant_context(module_id: str, question: str) -> str:
    # Question embedden
    query_embedding = embed(question)

    # Ähnliche vergangene Fragen finden
    similar = vector_search(query_embedding, module_id, limit=5)

    # Feedback zu diesen Fragen laden (KRITISCH!)
    feedback = get_feedback_for_messages(similar)

    return format_context(similar, feedback)
```

**Pro:** Findet thematisch relevanten Kontext
**Contra:** Benötigt Embedding-Pipeline

### Strategie 3: Hybrid (Empfohlen)

```python
def get_context(module_id: str, question: str) -> str:
    context_parts = []

    # 1. Immer: Architektur (struktureller Kontext)
    context_parts.append(get_architecture_context(module_id))

    # 2. Immer: Letzte Korrekturen (Fehler vermeiden!)
    context_parts.append(get_recent_feedback(module_id, limit=5))

    # 3. Semantisch: Ähnliche vergangene Fragen
    if has_vector_store(module_id):
        context_parts.append(get_similar_interactions(module_id, question))

    # 4. Recency: Letzte Events
    context_parts.append(get_recent_events(module_id, limit=5))

    return "\n\n".join(context_parts)
```

---

## Prompt-Aufbau

Der finale Prompt für die LLM sieht so aus:

```
Du hast Zugriff auf folgenden Kontext:

## Architektur: Vergabeprüfung
RAG-basierte Checklisten-Analyse für EFRE-Vorhaben

Tech-Stack: FastAPI, SQLAlchemy, ChromaDB
Patterns: Service Layer, Repository

### Komponenten:
- RAGService (service): Retrieval Augmented Generation
- ChecklistAnalyzer (service): Analysiert Prüfungschecklisten
- DocumentParser (util): Parst PDF/Word/Excel

### Architektur-Entscheidungen:
- "Warum RAG statt Fine-Tuning?": Domäne ändert sich häufig, RAG ermöglicht schnelle Updates

## ⚠️ Frühere Korrekturen (UNBEDINGT BEACHTEN!):
- Ursprüngliche Antwort: "Der DocumentParser unterstützt XLSX"
  Korrektur: FALSCH! XLSX-Support wurde erst in v1.2 hinzugefügt
  Problem: hallucination

## Letzte Änderungen:
- [15.01.2025] file_added: vergabe_checkliste.xlsx
- [14.01.2025] config_changed: llm_provider → anthropic

---

Aktuelle Frage: Wie füge ich eine neue Checklisten-Spalte hinzu?

Beachte unbedingt die früheren Korrekturen und wiederhole keine Fehler!
```

---

## Datenbank-Schema (Komplett)

```sql
-- =====================================================
-- MODUL-EVENTS
-- =====================================================
CREATE TABLE module_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_events_module_time ON module_events(module_id, created_at DESC);

-- =====================================================
-- ARCHITEKTUR
-- =====================================================
CREATE TABLE module_architecture (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id) UNIQUE,
    description TEXT,
    directory_structure JSONB DEFAULT '{}',
    tech_stack JSONB DEFAULT '{}',
    patterns JSONB DEFAULT '[]',
    version VARCHAR(20),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100)
);

CREATE TABLE architecture_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- service, model, api, util
    file_path VARCHAR(500),
    description TEXT,
    responsibilities JSONB DEFAULT '[]',
    public_interface JSONB DEFAULT '{}'
);
CREATE INDEX idx_components_module ON architecture_components(module_id);

CREATE TABLE component_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_component_id UUID REFERENCES architecture_components(id) ON DELETE CASCADE,
    target_component_id UUID REFERENCES architecture_components(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,  -- depends_on, uses, extends
    description TEXT,
    UNIQUE(source_component_id, target_component_id, relation_type)
);

CREATE TABLE architecture_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'accepted',  -- proposed, accepted, deprecated
    context TEXT,
    decision TEXT,
    alternatives JSONB DEFAULT '[]',
    consequences TEXT,
    superseded_by UUID REFERENCES architecture_decisions(id),
    decided_by VARCHAR(100),
    decided_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- LLM-KONVERSATIONEN
-- =====================================================
CREATE TABLE llm_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    session_name VARCHAR(200),
    context_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE llm_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES llm_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE llm_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES llm_messages(id) ON DELETE CASCADE UNIQUE,
    rating INTEGER,
    correction TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- DATEI-UPLOADS
-- =====================================================
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(50) REFERENCES modules(id),
    original_filename VARCHAR(500) NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),
    uploaded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_uploads(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE file_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_uploads(id) ON DELETE CASCADE,
    process_type VARCHAR(50),  -- parse, embed, chunk, ocr
    status VARCHAR(20),
    result_summary JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- =====================================================
-- OPTIONAL: VECTOR STORE FÜR SEMANTIC SEARCH
-- =====================================================
-- Wenn pgvector installiert ist:
-- CREATE EXTENSION IF NOT EXISTS vector;
--
-- CREATE TABLE interaction_embeddings (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     module_id VARCHAR(50) REFERENCES modules(id),
--     message_id UUID REFERENCES llm_messages(id),
--     content TEXT,
--     embedding vector(1536),  -- OpenAI ada-002
--     created_at TIMESTAMP DEFAULT NOW()
-- );
-- CREATE INDEX idx_embeddings ON interaction_embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## Workflow-Beispiel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. MODUL ERSTELLEN                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ → Event: module_created {name: "Vergabeprüfung"}                            │
│ → Architecture: Leeres Dokument angelegt                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. ARCHITEKTUR DEFINIEREN                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ → Architecture.tech_stack = {backend: ["FastAPI"], frontend: ["Vue3"]}      │
│ → Component: RAGService (service)                                           │
│ → Component: ChecklistAnalyzer (service)                                    │
│ → Relation: ChecklistAnalyzer --uses--> RAGService                          │
│ → ADR: "Warum RAG statt Fine-Tuning?"                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. DATEIEN HOCHLADEN                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ → Event: file_added {filename: "vergabe_checkliste.xlsx"}                   │
│ → FileUpload erstellt                                                       │
│ → ProcessingLog: parse → embed → chunk (jeweils mit Status)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. LLM-INTERAKTION                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ → Conversation erstellt                                                     │
│ → User: "Wie funktioniert die Checklisten-Analyse?"                         │
│ → Context wird geladen:                                                     │
│   - Architektur (Components, Relations, ADRs)                               │
│   - Letzte Events                                                           │
│   - Vorherige Korrekturen (falls vorhanden)                                 │
│ → LLM antwortet mit vollem Kontext                                          │
│ → Message gespeichert                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. FEEDBACK (KRITISCH!)                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ → User: "Das stimmt nicht, XLSX wird noch nicht unterstützt!"               │
│ → Feedback gespeichert:                                                     │
│   - rating: -1                                                              │
│   - correction: "XLSX-Support existiert nicht"                              │
│   - tags: ["hallucination"]                                                 │
│ → Event: llm_feedback erstellt                                              │
│                                                                             │
│ → NÄCHSTE ANFRAGE bekommt diese Korrektur als Kontext!                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. DEPLOYMENT                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ → Event: deployed {customer: "Kunde X", version: "1.2.0"}                   │
│ → Architecture-Snapshot für Version 1.2.0                                   │
│ → Conversation-Summary generiert                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API-Endpoints

### Architektur
```
GET  /api/v1/modules/{id}/architecture     → Architektur abrufen
PUT  /api/v1/modules/{id}/architecture     → Architektur aktualisieren
GET  /api/v1/modules/{id}/components       → Komponenten listen
POST /api/v1/modules/{id}/components       → Komponente hinzufügen
POST /api/v1/modules/{id}/relations        → Beziehung hinzufügen
POST /api/v1/modules/{id}/decisions        → ADR erstellen
POST /api/v1/modules/{id}/scan             → Auto-Erkennung der Struktur
```

### History & Events
```
GET  /api/v1/modules/{id}/timeline         → Event-Timeline
GET  /api/v1/modules/{id}/history          → Vollständige Geschichte
```

### Konversationen & Feedback
```
GET  /api/v1/conversations                 → Alle Konversationen
POST /api/v1/conversations                 → Neue Konversation
GET  /api/v1/conversations/{id}            → Eine Konversation
POST /api/v1/conversations/{id}/messages   → Nachricht hinzufügen
POST /api/v1/messages/{id}/feedback        → Feedback speichern
```

### Kontext
```
GET  /api/v1/context/{module_id}?question=...  → LLM-Kontext generieren
```

---

## Implementierungs-Prioritäten

| Phase | Komponente | Aufwand | Wert |
|-------|------------|---------|------|
| **1** | Events + Timeline | 2 Tage | Hoch |
| **1** | LLM-Messages + Feedback | 2 Tage | Kritisch |
| **2** | Architektur-Storage | 3 Tage | Hoch |
| **2** | Context-Service (Basic) | 2 Tage | Kritisch |
| **3** | File-Versioning | 2 Tage | Mittel |
| **3** | Auto-Scan | 1 Tag | Nice-to-have |
| **4** | Semantic Search | 3 Tage | Optional |

---

## Zusammenfassung

**Das Developer-Tool mit Memory ermöglicht:**

1. **Nachvollziehbarkeit** - Jede Änderung dokumentiert
2. **Konsistenz** - LLM kennt die Architektur
3. **Lernfähigkeit** - Korrekturen werden nicht wiederholt
4. **Kontext-Erhalt** - Auch nach Session-Wechsel

**Kernformel:**
```
Memory = Datenbank + Retrieval + Prompt-Logik
         (speichern)  (finden)    (einbinden)
```
