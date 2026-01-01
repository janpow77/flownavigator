# FlowNavigator Layer-Struktur und Rollen

## Organisations-Layer (Mandanten-Hierarchie)

Das System bildet eine hierarchische Organisationsstruktur ab:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEM-EBENE                                │
│                   (system_admin)                                │
│         Globaler Zugriff auf alle Konzerne & Behörden           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│  COORDINATION BODY A      │         │  COORDINATION BODY B      │
│  (Konzern, type="group")  │         │  (Konzern, type="group")  │
│  ─────────────────────    │         │  ─────────────────────    │
│  • group_admin            │         │  • group_admin            │
│  • authority_head         │         │  • authority_head         │
│  • team_leader            │         │  • team_leader            │
│  • auditor                │         │  • auditor                │
│  • viewer                 │         │  • viewer                 │
└───────────┬───────────────┘         └───────────┬───────────────┘
            │                                     │
    ┌───────┴───────┐                     ┌───────┴───────┐
    │               │                     │               │
    ▼               ▼                     ▼               ▼
┌─────────────┐ ┌─────────────┐     ┌─────────────┐ ┌─────────────┐
│Prüfbehörde A│ │Prüfbehörde B│     │Prüfbehörde C│ │Prüfbehörde D│
│(authority)  │ │(authority)  │     │(authority)  │ │(authority)  │
│─────────────│ │─────────────│     │─────────────│ │─────────────│
│• authority_ │ │• authority_ │     │• authority_ │ │• authority_ │
│  head       │ │  head       │     │  head       │ │  head       │
│• team_leader│ │• team_leader│     │• team_leader│ │• team_leader│
│• auditor    │ │• auditor    │     │• auditor    │ │• auditor    │
│• viewer     │ │• viewer     │     │• viewer     │ │• viewer     │
└─────────────┘ └─────────────┘     └─────────────┘ └─────────────┘
```

### Tenant-Modell (Datenbank)

```python
class Tenant:
    id: UUID
    name: str                    # z.B. "Bundesrechnungshof"
    type: "group" | "authority"  # Coordination Body oder Prüfbehörde
    parent_id: UUID | None       # Prüfbehörde → gehört zu Coordination Body
    status: "active" | "suspended" | "trial"
```

**Beispiel-Hierarchie:**
```
Coordination Body "EU-Prüfungskoordination" (type="group")
├── Prüfbehörde "Bundesrechnungshof" (type="authority", parent_id=Coordination Body)
├── Prüfbehörde "Landesrechnungshof Bayern" (type="authority", parent_id=Coordination Body)
└── Prüfbehörde "Landesrechnungshof NRW" (type="authority", parent_id=Coordination Body)
```

---

## Rollen pro Organisations-Layer

| Organisations-Layer | Rollen | Zugriffs-Scope |
|---------------------|--------|----------------|
| **System** | `system_admin` | Alle Coordination Bodies, alle Behörden, alle Daten |
| **Coordination Body** (Konzern) | `group_admin`, `authority_head`, `team_leader`, `auditor`, `viewer` | Eigener Konzern + alle untergeordneten Prüfbehörden |
| **Prüfbehörde** | `authority_head`, `team_leader`, `auditor`, `viewer` | Nur eigene Prüfbehörde |

### Rollen-Bedeutung je Ebene

| Rolle | Auf Coordination Body | Auf Prüfbehörde |
|-------|----------------------|-----------------|
| `group_admin` | Verwaltet den gesamten Konzern und alle Behörden | - (nicht auf Behörden-Ebene) |
| `authority_head` | Leitet Koordinationsstelle | Leitet Prüfbehörde |
| `team_leader` | Führt Konzern-weite Prüfteams | Führt Prüfteams in der Behörde |
| `auditor` | Prüfer auf Konzern-Ebene | Prüfer in der Behörde |
| `viewer` | Lesezugriff auf Konzern-Daten | Lesezugriff auf Behörden-Daten |

---

## Technische Architektur-Übersicht

Das FlowNavigator-Projekt (FlowAudit Platform) ist als **Monorepo** mit einer klaren Schichtenarchitektur aufgebaut:

```
┌─────────────────────────────────────────────────────┐
│         PRESENTATION LAYER (Vue 3 + TypeScript)     │
│                /apps/frontend/src                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│         SHARED PACKAGES LAYER (Domain & Adapters)   │
│    /packages (core, domain, documents, adapters)    │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              API LAYER (FastAPI, REST)              │
│              /apps/backend/app/api/                 │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│           SERVICE LAYER (Business Logic)            │
│           /apps/backend/app/services/               │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│        DATA ACCESS LAYER (Models & Schemas)         │
│        /apps/backend/app/models/ & /schemas/        │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│            DATABASE LAYER (PostgreSQL 15)           │
│              Migrations via Alembic                 │
└─────────────────────────────────────────────────────┘
```

---

## Rollen-Hierarchie

Das System definiert **6 Benutzerrollen** mit unterschiedlichen Berechtigungsstufen:

| Rolle | Hierarchie | Beschreibung |
|-------|------------|--------------|
| `system_admin` | 1 (Höchste) | System-Administrator |
| `group_admin` | 2 | Konzern-Administrator |
| `authority_head` | 3 | Behördenleitung |
| `team_leader` | 4 | Prüfteam-Leiter |
| `auditor` | 5 | Prüfer |
| `viewer` | 6 (Niedrigste) | Nur-Lesender Zugriff |

---

## Layer-Details mit Rollen-Berechtigungen

### 1. Presentation Layer (Frontend)

**Pfad:** `/apps/frontend/src`

**Technologien:** Vue 3, TypeScript, Pinia, Tailwind CSS

**Komponenten:**
- `components/` - Vue-Komponenten (Checklisten, Dokumente, Findings)
- `stores/auth.ts` - Authentifizierungs-State-Management
- `router/index.ts` - Routing mit Guards
- `views/` - Seiten-Komponenten

**Rollen-Zugriff auf diesem Layer:**

| Funktion | system_admin | group_admin | authority_head | team_leader | auditor | viewer |
|----------|:------------:|:-----------:|:--------------:|:-----------:|:-------:|:------:|
| Dashboard anzeigen | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Prüfungsfälle bearbeiten | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| Reports exportieren | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ |
| System-Einstellungen | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Benutzerverwaltung | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

---

### 2. Shared Packages Layer

**Pfad:** `/packages`

**Struktur:**
```
packages/
├── core/
│   ├── common/           # Gemeinsame Typen (@flowaudit/common)
│   └── validation/       # Validierungslogik
├── domain/
│   ├── checklists/       # Checklisten-Logik
│   └── group-queries/    # Konzern-Abfragen-Logik
├── documents/
│   └── document-box/     # Dokument-Box Logik
└── adapters/
    └── vue-adapter/      # Vue-spezifische Adapter
```

**Hinweis:** Dieser Layer enthält nur Geschäftslogik und Typen ohne direkte Authentifizierung. Berechtigungen werden in den darunterliegenden Layern geprüft.

---

### 3. API Layer

**Pfad:** `/apps/backend/app/api/`

**Endpoints:**
- `auth.py` - Authentifizierung (Login, Register, /me)
- `audit_cases.py` - CRUD für Prüfungsfälle
- `audit_logs.py` - Audit History
- `checklists.py` - Checklisten Management
- `findings.py` - Feststellungen
- `preferences.py` - Benutzer-Präferenzen

**Rollen-Zugriff auf API-Endpoints:**

| Endpoint | system_admin | group_admin | authority_head | team_leader | auditor | viewer |
|----------|:------------:|:-----------:|:--------------:|:-----------:|:-------:|:------:|
| `GET /audit-cases` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /audit-cases` | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| `PATCH /audit-cases/:id` | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| `DELETE /audit-cases/:id` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `POST /findings` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `POST /audit-cases/:id/approve` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `GET /reports` | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ |

**Legende:** ✅ = Vollzugriff | ⚠️ = Eingeschränkt | ❌ = Kein Zugriff

---

### 4. Service Layer

**Pfad:** `/apps/backend/app/services/`

**Komponenten:**
- `auth_service.py` - Authentifizierungslogik
- `module_service.py` - Modultransformation
- `llm/` - LLM Provider (OpenAI, Anthropic, Ollama)

**Sicherheitsfunktionen:**
- JWT Token-Erstellung und -Validierung
- Passwort-Hashing mit Bcrypt
- Rate Limiting (5/min Auth, 30/min Write, 100/min Read)

---

### 5. Data Access Layer

**Pfad:** `/apps/backend/app/models/` und `/schemas/`

**Modelle:**
- `user.py` - User Model mit Rollen
- `tenant.py` - Multi-Tenancy Model
- `audit_case.py` - Prüfungsfall-Modelle
- `audit_log.py` - Audit Trail
- `document_box.py` - Dokument-Verwaltung

**Multi-Tenancy:**
Alle Queries werden automatisch nach `tenant_id` des aktuellen Benutzers gefiltert:
```python
query = select(AuditCase).where(
    AuditCase.tenant_id == current_user.tenant_id
)
```

---

### 6. Database Layer

**Technologie:** PostgreSQL 15

**Wichtige Tabellen:**
- `tenants` - Mandanten (Konzerne, Behörden)
- `users` - Benutzer mit Rollen
- `audit_cases` - Prüfungsfälle
- `audit_logs` - Änderungsprotokoll

**Datenbank-Enums:**
```sql
CREATE TYPE user_role AS ENUM (
    'system_admin', 'group_admin', 'authority_head',
    'team_leader', 'auditor', 'viewer'
);

CREATE TYPE audit_case_status AS ENUM (
    'draft', 'in_progress', 'review', 'completed', 'archived'
);
```

---

## Rollen-Beschreibungen im Detail

### system_admin (System-Administrator)
- **Befugnisse:** Alle Operationen im gesamten System
- **Zugriff:** Alle Mandanten, alle Funktionen
- **Typische Aufgaben:**
  - System-Konfiguration
  - Globale Einstellungen
  - Mandanten-Verwaltung
  - Notfall-Zugriff

### group_admin (Konzern-Administrator)
- **Befugnisse:** Verwaltung innerhalb des eigenen Konzerns
- **Zugriff:** Eigener Mandant und untergeordnete Behörden
- **Typische Aufgaben:**
  - Benutzerverwaltung
  - Fiscaljahr-Konfiguration
  - Konzern-Reporting
  - Behörden-Zuordnung

### authority_head (Behördenleitung)
- **Befugnisse:** Strategische Steuerung der Prüfungen
- **Zugriff:** Eigene Behörde
- **Typische Aufgaben:**
  - Prüfstrategie festlegen
  - Prüffälle genehmigen
  - Berichtswesen überwachen
  - Ressourcenplanung

### team_leader (Prüfteam-Leiter)
- **Befugnisse:** Operative Führung des Prüfteams
- **Zugriff:** Zugewiesene Prüfungsfälle
- **Typische Aufgaben:**
  - Prüffall-Zuweisung
  - Team-Koordination
  - Review und Genehmigung
  - Qualitätssicherung

### auditor (Prüfer)
- **Befugnisse:** Durchführung von Prüfungen
- **Zugriff:** Zugewiesene Prüfungsfälle (nur Bearbeitung)
- **Typische Aufgaben:**
  - Checklisten ausfüllen
  - Findings erfassen
  - Dokumente hochladen
  - Prüfungsnotizen erstellen

### viewer (Nur-Lesender Zugriff)
- **Befugnisse:** Nur Ansicht von Daten
- **Zugriff:** Dashboards und Reports (nur lesen)
- **Typische Aufgaben:**
  - Dashboards ansehen
  - Reports lesen
  - Statistiken einsehen
  - Keine Änderungen möglich

---

## Authentifizierungs-Flow

```
1. POST /api/auth/login (Email + Passwort)
          ↓
2. Backend validiert Credentials
          ↓
3. JWT Token wird erstellt:
   {
     "sub": user_id,
     "tenant_id": tenant_id,
     "role": user_role,
     "exp": expire_time
   }
          ↓
4. Token im Authorization Header:
   Authorization: Bearer <token>
          ↓
5. Jeder Request: get_current_user() validiert Token
          ↓
6. Tenant-Filter auf alle Datenbank-Queries
```

---

## Sicherheits-Features

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| JWT Authentication | ✅ | HS256 signierte Tokens |
| Password Hashing | ✅ | Bcrypt mit Salt |
| Multi-Tenant Isolation | ✅ | tenant_id Filter auf alle Queries |
| Audit Trail | ✅ | Alle Änderungen werden geloggt |
| Rate Limiting | ✅ | Auth: 5/min, Write: 30/min, Read: 100/min |
| CORS | ✅ | Konfiguriert im Backend |
| RBAC | ✅ | 6-stufige Rollen-Hierarchie |
| HTTPS | ⚠️ | Für Production erforderlich |

---

## Zusammenfassung: Welche Admins auf welchem Layer?

### Organisations-Layer × Rollen Matrix

```
                    │ system │ group  │authority│ team   │        │
                    │ _admin │ _admin │ _head   │_leader │auditor │viewer
────────────────────┼────────┼────────┼─────────┼────────┼────────┼──────
SYSTEM-EBENE        │  R/W   │   -    │    -    │   -    │   -    │  -
────────────────────┼────────┼────────┼─────────┼────────┼────────┼──────
COORDINATION BODY   │  R/W   │  R/W   │   R/W   │  R/W   │  R/W   │  R
(type="group")      │        │        │         │        │(nur    │
                    │        │        │         │        │zugewi.)│
────────────────────┼────────┼────────┼─────────┼────────┼────────┼──────
PRÜFBEHÖRDE A       │  R/W   │  R/W   │   R/W   │  R/W   │  R/W   │  R
(type="authority")  │        │        │         │        │(nur    │
                    │        │        │         │        │zugewi.)│
────────────────────┼────────┼────────┼─────────┼────────┼────────┼──────
PRÜFBEHÖRDE B       │  R/W   │  R/W   │   R/W   │  R/W   │  R/W   │  R
(type="authority")  │        │        │         │        │(nur    │
                    │        │        │         │        │zugewi.)│
────────────────────┴────────┴────────┴─────────┴────────┴────────┴──────

R = Lesen, W = Schreiben, - = Kein Zugriff
```

**Hinweis:** Sowohl Coordination Body als auch Prüfbehörden haben dieselben Rollen.
Der Unterschied liegt im Scope:
- Rollen auf **Coordination Body** haben Zugriff auf den Konzern UND alle untergeordneten Behörden
- Rollen auf **Prüfbehörde** haben nur Zugriff auf die eigene Behörde

### Technische Layer × Rollen

| Technischer Layer | system_admin | group_admin | authority_head | team_leader | auditor | viewer |
|-------------------|:------------:|:-----------:|:--------------:|:-----------:|:-------:|:------:|
| **Presentation** | Alles | Konzern-UI | Behörden-UI | Team-UI | Prüfer-UI | Nur-Lese-UI |
| **API** | Alle Endpoints | Konzern-Endpoints | Behörden-Endpoints | Team-Endpoints | Prüf-Endpoints | GET only |
| **Service** | Konfiguration | Reporting | Genehmigung | Zuweisung | Bearbeitung | - |
| **Data Access** | Alle Tenants | Eigener Konzern | Eigene Behörde | Eigene Behörde | Eigene Behörde | Eigene Behörde |
| **Database** | Direkt-Zugriff | Via API | Via API | Via API | Via API | Via API |

### Wer verwaltet wen?

| Rolle | Kann verwalten | Wird verwaltet von |
|-------|----------------|-------------------|
| `system_admin` | Alles (Coordination Bodies, Behörden, Benutzer) | - |
| `group_admin` | Coordination Body, alle Behörden im Konzern, Benutzer | `system_admin` |
| `authority_head` | Eigene Ebene (Coordination Body ODER Behörde), Teams, Prüfer | `group_admin`, `system_admin` |
| `team_leader` | Prüfungsfälle, Prüfer-Zuweisungen | `authority_head` |
| `auditor` | Eigene Prüfungsfälle | `team_leader` |
| `viewer` | Nichts (nur lesen) | `authority_head` |

### Beispiel: Benutzer-Zuordnung

```
Coordination Body "EU-Prüfungskoordination"
├── Max Müller (group_admin) ─────────── Verwaltet gesamten Konzern
├── Anna Schmidt (authority_head) ────── Leitet die Koordinationsstelle
├── Peter Weber (team_leader) ────────── Führt Konzern-übergreifendes Team
├── Lisa Koch (auditor) ──────────────── Prüferin auf Konzern-Ebene
├── Tom Braun (viewer) ───────────────── Lesezugriff auf Konzern
│
├── Prüfbehörde "Bundesrechnungshof"
│   ├── Sabine Meier (authority_head) ── Leitet den Bundesrechnungshof
│   ├── Klaus Fischer (team_leader) ──── Führt Prüfteam
│   ├── Julia Bauer (auditor) ────────── Prüferin
│   └── Michael Wolf (viewer) ────────── Lesezugriff
│
└── Prüfbehörde "Landesrechnungshof Bayern"
    ├── Eva Schwarz (authority_head) ─── Leitet LRH Bayern
    ├── Dirk Hoffmann (team_leader) ──── Führt Prüfteam
    └── Nina Schulz (auditor) ─────────── Prüferin
```
