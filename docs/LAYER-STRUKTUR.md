# FlowNavigator Layer-Struktur und Rollen

## Architektur-Übersicht

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

| Layer | Erforderliche Rollen für Änderungen |
|-------|-------------------------------------|
| **Presentation** | Alle Rollen (Frontend zeigt/versteckt UI basierend auf Rolle) |
| **Shared Packages** | Keine Authentifizierung (nur Bibliotheken) |
| **API** | Abhängig vom Endpoint (siehe Tabelle oben) |
| **Service** | `system_admin` für Konfiguration, andere für Business Logic |
| **Data Access** | Automatische Tenant-Isolation für alle Rollen |
| **Database** | Nur `system_admin` für direkte DB-Änderungen |
