# Umsetzung mit Claude CLI

Dieses Dokument enthält alle Implementierungsaufgaben für FlowNavigator, strukturiert für die Ausführung mit Claude CLI.

---

## Übersicht aller Features

| # | Feature | Priorität | Aufwand | Status |
|---|---------|-----------|---------|--------|
| 1 | **Layer 0: Vendor & Development Module** | Hoch | 3-4 Wochen | ⬜ Offen |
| 2 | **Layer 1: Coordination Body Admin** | Hoch | 2-3 Wochen | ⬜ Offen |
| 3 | **Layer 2: Authority Admin** | Mittel | 1-2 Wochen | ⬜ Offen |
| 4 | **Layer-Dashboard (Hierarchie)** | Hoch | 2-3 Wochen | ⬜ Offen |
| 5 | **UI Enhancements** | Hoch | 3 Wochen | ⬜ Offen (Radial ✅) |
| 6 | **Modul-Distribution-System** | Hoch | 2 Wochen | ⬜ Offen |
| 7 | **Workflow-Historisierung** | Mittel | 1.5 Wochen | ⬜ Offen |

**Gesamtaufwand: ~15-19 Wochen**

---

## 1. Layer 0: Vendor & Development Module

### 1.1 Backend-Modelle

```
Dateien:
- apps/backend/app/models/vendor.py (NEU)
- apps/backend/app/models/customer.py (NEU)
- apps/backend/app/models/module.py (NEU)
```

#### Vendor-Modelle
- [ ] `Vendor` - Softwarefirma (name, contact_email, billing_email, address)
- [ ] `VendorUser` - Vendor-Mitarbeiter mit Rollen

#### Vendor-Rollen (in user.py erweitern)
- [ ] `vendor_admin` - Vollzugriff auf alle Kunden
- [ ] `vendor_support` - Lesezugriff für Support
- [ ] `vendor_developer` - Modul-Entwicklung
- [ ] `vendor_qa` - Quality Assurance, Testing

#### Customer-Modelle
- [ ] `Customer` - Kunden mit Lizenzvertrag
  - tenant_id, contract_number, contract_start/end
  - licensed_users, licensed_authorities
  - billing_contact, billing_address, payment_method
  - status: active | suspended | trial | terminated
- [ ] `LicenseUsage` - Tägliche Lizenz-Snapshots
- [ ] `LicenseAlert` - Warnungen bei Überschreitung

#### Development-Modelle
- [ ] `Module` - Software-Module
  - name, version, description
  - status: development | testing | released | deprecated
  - dependencies, min_system_version, feature_flags
- [ ] `ModuleDeployment` - Deployment an Kunden
  - module_id, customer_id
  - status: pending | deploying | deployed | failed | rolled_back
  - deployed_version, previous_version
- [ ] `ReleaseNote` - Release-Notes pro Version
  - title, changes[], breaking_changes[], published_at

### 1.2 Pydantic Schemas

```
Dateien:
- apps/backend/app/schemas/vendor.py (NEU)
- apps/backend/app/schemas/customer.py (NEU)
- apps/backend/app/schemas/module.py (NEU)
```

- [ ] VendorCreate, VendorUpdate, VendorResponse
- [ ] VendorUserCreate, VendorUserResponse
- [ ] CustomerCreate, CustomerUpdate, CustomerResponse
- [ ] LicenseUsageResponse, LicenseAlertResponse
- [ ] ModuleCreate, ModuleUpdate, ModuleResponse
- [ ] ModuleDeploymentCreate, ModuleDeploymentResponse
- [ ] ReleaseNoteCreate, ReleaseNoteResponse

### 1.3 Datenbank-Migrationen

```
Dateien:
- apps/backend/alembic/versions/xxx_add_vendor_layer.py
- apps/backend/alembic/versions/xxx_add_customer_licensing.py
- apps/backend/alembic/versions/xxx_add_modules.py
```

- [ ] Vendor-Tabellen erstellen
- [ ] VendorUser-Tabelle mit Rollen-Enum erweitern
- [ ] Customer-Tabellen mit Lizenzfeldern
- [ ] LicenseUsage + LicenseAlert Tabellen
- [ ] Module + ModuleDeployment + ReleaseNote Tabellen
- [ ] Fremdschlüssel-Beziehungen

### 1.4 API-Endpoints

```
Dateien:
- apps/backend/app/api/vendor.py (NEU)
- apps/backend/app/api/customers.py (NEU)
- apps/backend/app/api/modules.py (NEU)
- apps/backend/app/api/licenses.py (NEU)
```

#### Vendor-API
- [ ] `GET /api/v1/vendor` - Vendor-Infos
- [ ] `PUT /api/v1/vendor` - Vendor aktualisieren
- [ ] `GET /api/v1/vendor/users` - Vendor-User auflisten
- [ ] `POST /api/v1/vendor/users` - Vendor-User erstellen
- [ ] `PUT /api/v1/vendor/users/{id}` - Vendor-User bearbeiten
- [ ] `DELETE /api/v1/vendor/users/{id}` - Vendor-User deaktivieren

#### Customers-API
- [ ] `GET /api/v1/customers` - Alle Kunden
- [ ] `POST /api/v1/customers` - Neuen Kunden anlegen
- [ ] `GET /api/v1/customers/{id}` - Kunden-Details
- [ ] `PUT /api/v1/customers/{id}` - Kunden aktualisieren
- [ ] `DELETE /api/v1/customers/{id}` - Kunden deaktivieren
- [ ] `GET /api/v1/customers/{id}/authorities` - Behörden des Kunden
- [ ] `GET /api/v1/customers/{id}/licenses` - Lizenz-Historie
- [ ] `POST /api/v1/customers/{id}/licenses/adjust` - Lizenzen anpassen

#### Module-API (Development)
- [ ] `GET /api/v1/modules` - Alle Module
- [ ] `POST /api/v1/modules` - Neues Modul erstellen
- [ ] `GET /api/v1/modules/{id}` - Modul-Details
- [ ] `PUT /api/v1/modules/{id}` - Modul aktualisieren
- [ ] `POST /api/v1/modules/{id}/release` - Modul releasen
- [ ] `GET /api/v1/modules/{id}/deployments` - Deployments
- [ ] `POST /api/v1/modules/{id}/deploy` - An Kunden deployen
- [ ] `POST /api/v1/modules/{id}/rollback` - Rollback

### 1.5 Frontend: Vendor-Portal

```
Dateien:
- apps/frontend/src/views/VendorDashboard.vue (NEU)
- apps/frontend/src/views/CustomerManagement.vue (NEU)
- apps/frontend/src/views/ModuleManagement.vue (NEU)
- apps/frontend/src/stores/vendor.ts (NEU)
```

#### Views
- [ ] `VendorDashboard.vue` - Übersicht (Kunden, Lizenzen, Module)
- [ ] `CustomerManagement.vue` - Kunden-CRUD
- [ ] `CustomerDetail.vue` - Kunden-Details mit Lizenzen
- [ ] `ModuleManagement.vue` - Modul-Entwicklung
- [ ] `ModuleDetail.vue` - Modul mit Deployments

#### Komponenten
- [ ] `CustomerCard.vue` - Kunden-Kachel
- [ ] `LicenseGauge.vue` - Lizenz-Auslastung (Gauge-Chart)
- [ ] `ModuleCard.vue` - Modul-Karte
- [ ] `DeploymentTimeline.vue` - Deployment-Historie

#### Store
- [ ] `vendor.ts` Pinia Store
  - State: customers, modules, selectedCustomer
  - Actions: fetchCustomers, createCustomer, deployModule

---

## 2. Layer 1: Coordination Body Admin

### 2.1 Backend-Modelle

```
Dateien:
- apps/backend/app/models/profile.py (NEU)
```

- [ ] `CoordinationBodyProfile` - CB-Stammdaten
  - tenant_id (FK)
  - official_name, short_name
  - street, postal_code, city, country
  - phone, email, website
  - logo_url, primary_color, secondary_color

### 2.2 API-Endpoints

```
Dateien:
- apps/backend/app/api/profiles.py (NEU)
```

- [ ] `GET /api/v1/tenants/{id}/profile` - Profil abrufen
- [ ] `PUT /api/v1/tenants/{id}/profile` - Profil aktualisieren
- [ ] `POST /api/v1/tenants/{id}/profile/logo` - Logo hochladen

### 2.3 Frontend: CB-Admin-Portal

```
Dateien:
- apps/frontend/src/views/TenantAdmin.vue (NEU)
- apps/frontend/src/components/admin/ProfileEditor.vue (NEU)
```

#### TenantAdmin.vue Tabs
- [ ] Tab: Prüfbehörden (AuthorityList.vue)
- [ ] Tab: Benutzer (UserManager.vue)
- [ ] Tab: Templates (TenantTemplates.vue)
- [ ] Tab: Stammdaten (ProfileEditor.vue)
- [ ] Tab: Lizenzen (LicenseAllocation.vue)

#### Komponenten
- [ ] `AuthorityList.vue` - Behörden verwalten
- [ ] `UserManager.vue` - Benutzer CRUD
- [ ] `TenantTemplates.vue` - Templates überschreiben
- [ ] `ProfileEditor.vue` - Stammdaten bearbeiten
- [ ] `LicenseAllocation.vue` - Lizenzen an Behörden verteilen

---

## 3. Layer 2: Authority Admin

### 3.1 Backend-Modelle

```
Dateien:
- apps/backend/app/models/profile.py (erweitern)
```

- [ ] `AuthorityProfile` - Behörden-Stammdaten
  - tenant_id (FK)
  - official_name, short_name, authority_type
  - Adresse, Kontakt, Logo/Farben

### 3.2 Frontend: Authority-Admin

```
Dateien:
- apps/frontend/src/views/AuthorityAdmin.vue (NEU)
```

#### Tabs
- [ ] Tab: Benutzer (UserManager.vue)
- [ ] Tab: Teams (TeamManager.vue)
- [ ] Tab: Templates (AuthorityTemplates.vue)
- [ ] Tab: Stammdaten (ProfileEditor.vue)

---

## 4. Layer-Dashboard (Hierarchie-Visualisierung)

### 4.1 Backend-API

```
Dateien:
- apps/backend/app/api/dashboard.py (erweitern)
```

- [ ] `GET /api/v1/dashboard/layers` - Gesamt-Hierarchie
- [ ] `GET /api/v1/dashboard/layers/{customer_id}` - Kunden-Detail
- [ ] `GET /api/v1/dashboard/layers/{customer_id}/authorities/{id}` - Behörden-Detail

#### Response-Struktur
```json
{
  "vendor": { "name": "...", "stats": {...} },
  "customers": [
    {
      "id": "...",
      "name": "EU-Prüfkoordination",
      "licensed_users": 50,
      "active_users": 43,
      "authorities": [
        { "id": "...", "name": "BRH", "user_count": 15 }
      ]
    }
  ]
}
```

### 4.2 Frontend: Layer-Dashboard

```
Dateien:
- apps/frontend/src/views/LayerDashboard.vue (NEU)
- apps/frontend/src/components/dashboard/LayerTree.vue (NEU)
- apps/frontend/src/stores/layerDashboard.ts (NEU)
```

- [ ] `LayerDashboard.vue` - Hauptansicht
- [ ] `LayerTree.vue` - Hierarchie-Baum mit Expand/Collapse
- [ ] `VendorCard.vue` - Layer 0 Übersicht
- [ ] `CustomerCard.vue` - Layer 1 Kacheln
- [ ] `AuthorityNode.vue` - Layer 2 Knoten
- [ ] `StatsCard.vue` - Kennzahlen
- [ ] `StatusBadge.vue` - Status-Indikator

#### Pinia Store
- [ ] `layerDashboard.ts`
  - State: dashboardData, expandedCustomers, selectedEntity
  - Actions: fetchDashboard, fetchCustomerDetail
  - Getters: selectedCustomer, selectedAuthority

#### Router
- [ ] `/admin/dashboard` → LayerDashboard.vue
- [ ] `/admin/customers/:id` → CustomerDetail.vue
- [ ] `/admin/customers/:id/authorities/:aid` → AuthorityDetail.vue

---

## 5. UI Enhancements

### 5.1 Shimmer Loader (1 Woche)

```
Dateien:
- apps/frontend/src/styles/themes.css (erweitern)
- apps/frontend/src/components/common/SkeletonLoader.vue (NEU)
- apps/frontend/src/components/common/SkeletonTable.vue (NEU)
- apps/frontend/src/components/common/SkeletonCard.vue (NEU)
```

- [ ] CSS: `@keyframes shimmer`, `@keyframes pulse-subtle`
- [ ] CSS: `.skeleton`, `.skeleton-text`, `.skeleton-avatar`, `.skeleton-card`
- [ ] CSS: `@media (prefers-reduced-motion)` Accessibility
- [ ] `SkeletonLoader.vue` - Basis-Komponente
- [ ] `SkeletonTable.vue` - Tabellen-Skeleton
- [ ] `SkeletonCard.vue` - Karten-Skeleton
- [ ] `SkeletonStats.vue` - Stats-Skeleton
- [ ] Integration in AuditCasesView, DashboardView, GroupQueriesView
- [ ] Delayed Skeleton (200ms Verzögerung)

### 5.2 Microinteractions (1 Woche)

```
Dateien:
- apps/frontend/src/composables/useRipple.ts (NEU)
- apps/frontend/src/composables/useButtonState.ts (NEU)
- apps/frontend/src/composables/useToast.ts (NEU)
- apps/frontend/src/components/common/EnhancedButton.vue (NEU)
- apps/frontend/src/components/common/ValidatedInput.vue (NEU)
- apps/frontend/src/components/common/Toast.vue (NEU)
- apps/frontend/src/components/common/CopyButton.vue (NEU)
```

- [ ] `useRipple.ts` - Ripple-Effekt
- [ ] `useButtonState.ts` - Loading/Success/Error States
- [ ] `useToast.ts` - Toast Composable
- [ ] `EnhancedButton.vue` - Button mit Feedback
- [ ] `ValidatedInput.vue` - Input mit Validierung
- [ ] `Toast.vue` + `ToastContainer.vue` - Toast-System
- [ ] `CopyButton.vue` - Copy-to-Clipboard

### 5.3 Radial View ✅ FERTIG

> Bereits implementiert in `apps/frontend/src/components/views/RadialView.vue`

- [x] SVG-basierte Darstellung
- [x] Color Picker (7 Presets)
- [x] Zoom Controls (50%-150%)
- [x] Pulse-Ring Animationen
- [x] Hover-Info-Panel
- [x] LocalStorage Persistenz

### 5.4 View-Switcher Dropdown (0.5 Wochen)

```
Dateien:
- apps/frontend/src/components/common/ViewSwitcher.vue (NEU)
```

- [ ] Dropdown für alle 5 Views (Tiles, List, Tree, Radial, Minimal)
- [ ] Icon + Label pro Option
- [ ] Keyboard-Navigation (Arrow, Enter, Escape)
- [ ] LocalStorage pro Route
- [ ] Integration in DashboardView, AuditCasesView, GroupQueriesView

---

## 6. Modul-Distribution-System

### 6.1 Backend

```
Dateien:
- apps/backend/app/core/module_manager.py (NEU)
- apps/backend/app/api/modules.py (erweitern)
- modules/vp_ai/module.json (NEU)
```

- [ ] `module.json` Schema definieren
- [ ] `ModuleManager` Klasse
  - list_installed(), get_available()
  - install_module(), update_module(), uninstall_module()
  - get_module_config(), set_module_config()
- [ ] API: GET/POST /api/v1/modules/*

### 6.2 Paket-Format (.adbpkg)

- [ ] ZIP-Struktur mit Manifest
- [ ] Build-Script für Paket-Erstellung
- [ ] Signatur/Checksum für Integrität

---

## 7. Workflow-Historisierung

### 7.1 Backend-Modelle

```
Dateien:
- apps/backend/app/models/module_history.py (NEU)
- apps/backend/app/models/module_architecture.py (NEU)
- apps/backend/app/models/llm_history.py (NEU)
```

- [ ] `ModuleEvent` - Events in Modul-Geschichte
- [ ] `ModuleArchitecture` - Architektur-Dokument
- [ ] `ArchitectureComponent` - Komponenten
- [ ] `ArchitectureDecision` - ADRs
- [ ] `LLMConversation` - LLM-Sessions
- [ ] `LLMMessage` - Nachrichten
- [ ] `LLMFeedback` - User-Feedback

### 7.2 Context-Service

```
Datei: apps/backend/app/services/context_service.py (NEU)
```

- [ ] `get_module_context(module_id)` - Vollständige Geschichte
- [ ] `get_conversation_context(session_id, limit)` - Letzte N Nachrichten
- [ ] `build_llm_prompt_with_context(question, module_id)` - Prompt mit Kontext

---

## Gap-Analyse Status

```
LAYER 0: VENDOR                                              0% ░░░░░░░░░
❌ Vendor-Modell          ❌ Lizenz-Tracking        ❌ Development-Module

LAYER 1: COORDINATION BODY                                  40% ████░░░░░
✅ Tenant (type=group)    ❌ CB-Profile             ❌ Konzern-Admin-Portal

LAYER 2: PRÜFBEHÖRDE                                        50% █████░░░░
✅ Tenant (type=authority) ❌ Authority-Profile      ❌ Behörden-Admin

PRÜFFALL-EBENE                                              75% ███████░░
✅ AuditCase               ✅ Checklisten            ✅ Findings
```

---

## Befehle für Claude CLI

### 1. Layer 0 starten:
```
Implementiere Layer 0 (Vendor & Development Module) basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md (Abschnitt 1).

Beginne mit:
1. Vendor-Modell in apps/backend/app/models/vendor.py
2. Customer-Modell in apps/backend/app/models/customer.py
3. Rollen-Enum erweitern (vendor_admin, vendor_support, vendor_developer, vendor_qa)
4. Alembic-Migration erstellen
```

### 2. Layer-Dashboard starten:
```
Implementiere das Layer-Dashboard basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md (Abschnitt 4).

Beginne mit:
1. Dashboard-API in apps/backend/app/api/dashboard.py erweitern
2. LayerDashboard.vue erstellen
3. LayerTree.vue Komponente
4. Pinia Store layerDashboard.ts
```

### 3. UI Enhancements starten:
```
Implementiere UI Enhancements basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md (Abschnitt 5).

Beginne mit:
1. Shimmer CSS in themes.css
2. SkeletonLoader.vue Basis-Komponente
3. ViewSwitcher.vue Dropdown
4. Integration in bestehende Views
```

---

## Abhängigkeiten

```
Layer 0 (Vendor/Customer)
    │
    ├──────────────────┬──────────────────┐
    │                  │                  │
    ▼                  ▼                  ▼
Layer 1 (CB)     Layer-Dashboard    Development Module
    │                  │
    ▼                  │
Layer 2 (Auth)         │
    │                  │
    └──────────────────┘
            │
            ▼
    UI Enhancements
```

---

*Dokumentation erstellt aus: LAYER-STRUKTUR.md, 02_IMPLEMENTATION_TASKS.md*
*Referenz: Gap-Analyse zeigt ~55-60% Implementierungs-Status*
