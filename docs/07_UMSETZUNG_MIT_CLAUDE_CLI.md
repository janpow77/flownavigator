# Umsetzung mit Claude CLI

Vollständiger Implementierungsplan für FlowNavigator mit Akzeptanzkriterien und Tests.

---

## Gesamtübersicht

| # | Feature | Priorität | Aufwand | Status |
|---|---------|-----------|---------|--------|
| 1 | Layer 0: Vendor & Development Module | Hoch | 3-4 Wochen | ⬜ Offen |
| 2 | Layer 1: Coordination Body (Konzern) | Hoch | 2-3 Wochen | ⬜ Offen |
| 3 | Layer 2: Prüfbehörde Admin | Mittel | 1-2 Wochen | ⬜ Offen |
| 4 | Layer-Dashboard (Hierarchie) | Hoch | 2-3 Wochen | ⬜ Offen |
| 5 | UI Enhancements | Hoch | 3 Wochen | ⬜ Offen (Radial ✅) |
| 6 | Modul-Distribution-System | Hoch | 2 Wochen | ⬜ Offen |
| 7 | Workflow-Historisierung | Mittel | 1.5 Wochen | ⬜ Offen |

**Gesamtaufwand: ~15-19 Wochen**

---

## Referenz-Dokumente

- `docs/LAYER-STRUKTUR.md` - Vollständige Layer-Architektur
- `docs/02_IMPLEMENTATION_TASKS.md` - Detaillierte Implementierungsaufgaben
- `docs/04_KONZEPT_DEVELOPER_MEMORY.md` - LLM-Kontext-Konzept

---

# Feature 1: Layer 0 - Vendor & Development Module

## 1.1 Backend-Modelle

### Aufgaben

```
Dateien:
- apps/backend/app/models/vendor.py (NEU)
- apps/backend/app/models/customer.py (NEU)
- apps/backend/app/models/module.py (NEU)
- apps/backend/app/models/user.py (ERWEITERN)
```

#### 1.1.1 Vendor-Modelle
- [ ] `Vendor` Model erstellen
  - id: UUID (PK)
  - name: str (z.B. "FlowAudit GmbH")
  - contact_email: str
  - billing_email: str
  - address_street, address_city, address_postal_code, address_country
  - created_at, updated_at

- [ ] `VendorUser` Model erstellen
  - id: UUID (PK)
  - vendor_id: UUID (FK → Vendor)
  - email: str (unique)
  - hashed_password: str
  - role: VendorRole Enum
  - first_name, last_name
  - is_active: bool
  - created_at, updated_at

#### 1.1.2 Rollen-Enum erweitern
- [ ] `VendorRole` Enum in user.py hinzufügen:
  ```python
  class VendorRole(str, Enum):
      vendor_admin = "vendor_admin"
      vendor_support = "vendor_support"
      vendor_developer = "vendor_developer"
      vendor_qa = "vendor_qa"
  ```

#### 1.1.3 Customer-Modelle
- [ ] `Customer` Model erstellen
  - id: UUID (PK)
  - tenant_id: UUID (FK → Tenant)
  - contract_number: str (unique)
  - contract_start: date
  - contract_end: date | None
  - licensed_users: int
  - licensed_authorities: int
  - billing_contact: str
  - billing_email: str
  - billing_address_*: str
  - payment_method: str
  - status: CustomerStatus Enum (active, suspended, trial, terminated)
  - created_at, updated_at

- [ ] `LicenseUsage` Model erstellen
  - id: UUID (PK)
  - customer_id: UUID (FK → Customer)
  - date: date
  - active_users: int
  - active_authorities: int
  - created_at

- [ ] `LicenseAlert` Model erstellen
  - id: UUID (PK)
  - customer_id: UUID (FK → Customer)
  - alert_type: str (warning, critical, exceeded)
  - message: str
  - threshold_percent: int
  - current_percent: int
  - acknowledged: bool
  - created_at

#### 1.1.4 Development-Modelle
- [ ] `Module` Model erstellen
  - id: UUID (PK)
  - name: str
  - version: str
  - description: str
  - status: ModuleStatus Enum (development, testing, released, deprecated)
  - developed_by: UUID (FK → VendorUser)
  - released_at: datetime | None
  - dependencies: JSON (list[str])
  - min_system_version: str
  - feature_flags: JSON (dict)
  - created_at, updated_at

- [ ] `ModuleDeployment` Model erstellen
  - id: UUID (PK)
  - module_id: UUID (FK → Module)
  - customer_id: UUID (FK → Customer)
  - status: DeploymentStatus Enum (pending, deploying, deployed, failed, rolled_back)
  - deployed_at: datetime | None
  - deployed_by: UUID (FK → VendorUser)
  - deployed_version: str
  - previous_version: str | None
  - error_message: str | None
  - created_at

- [ ] `ReleaseNote` Model erstellen
  - id: UUID (PK)
  - module_id: UUID (FK → Module)
  - version: str
  - title: str
  - changes: JSON (list[str])
  - breaking_changes: JSON (list[str])
  - published_at: datetime
  - created_at

### Akzeptanzkriterien 1.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-1.1.1 | Vendor kann erstellt werden | `test_create_vendor` |
| AC-1.1.2 | VendorUser kann mit allen 4 Rollen erstellt werden | `test_create_vendor_user_all_roles` |
| AC-1.1.3 | Customer mit Lizenzinfos kann erstellt werden | `test_create_customer_with_licenses` |
| AC-1.1.4 | LicenseUsage wird täglich getrackt | `test_license_usage_tracking` |
| AC-1.1.5 | LicenseAlert wird bei >80% Auslastung erstellt | `test_license_alert_threshold` |
| AC-1.1.6 | Module kann erstellt und released werden | `test_module_lifecycle` |
| AC-1.1.7 | ModuleDeployment tracked Status korrekt | `test_module_deployment_status` |
| AC-1.1.8 | ReleaseNote wird bei Release erstellt | `test_release_note_creation` |

### Tests 1.1

```python
# apps/backend/tests/models/test_vendor.py

import pytest
from app.models.vendor import Vendor, VendorUser, VendorRole
from app.models.customer import Customer, LicenseUsage, LicenseAlert, CustomerStatus

class TestVendorModels:

    def test_create_vendor(self, db_session):
        """AC-1.1.1: Vendor kann erstellt werden"""
        vendor = Vendor(
            name="FlowAudit GmbH",
            contact_email="support@flowaudit.de",
            billing_email="billing@flowaudit.de",
            address_city="Berlin"
        )
        db_session.add(vendor)
        db_session.commit()

        assert vendor.id is not None
        assert vendor.name == "FlowAudit GmbH"

    def test_create_vendor_user_all_roles(self, db_session, vendor):
        """AC-1.1.2: VendorUser kann mit allen 4 Rollen erstellt werden"""
        roles = [
            VendorRole.vendor_admin,
            VendorRole.vendor_support,
            VendorRole.vendor_developer,
            VendorRole.vendor_qa
        ]

        for role in roles:
            user = VendorUser(
                vendor_id=vendor.id,
                email=f"{role.value}@flowaudit.de",
                role=role,
                first_name="Test",
                last_name=role.value
            )
            db_session.add(user)

        db_session.commit()

        users = db_session.query(VendorUser).filter_by(vendor_id=vendor.id).all()
        assert len(users) == 4
        assert set(u.role for u in users) == set(roles)

    def test_create_customer_with_licenses(self, db_session, tenant):
        """AC-1.1.3: Customer mit Lizenzinfos kann erstellt werden"""
        customer = Customer(
            tenant_id=tenant.id,
            contract_number="2024-CB-001",
            licensed_users=50,
            licensed_authorities=5,
            status=CustomerStatus.active
        )
        db_session.add(customer)
        db_session.commit()

        assert customer.licensed_users == 50
        assert customer.licensed_authorities == 5

    def test_license_usage_tracking(self, db_session, customer):
        """AC-1.1.4: LicenseUsage wird täglich getrackt"""
        from datetime import date

        usage = LicenseUsage(
            customer_id=customer.id,
            date=date.today(),
            active_users=43,
            active_authorities=3
        )
        db_session.add(usage)
        db_session.commit()

        assert usage.active_users == 43

    def test_license_alert_threshold(self, db_session, customer):
        """AC-1.1.5: LicenseAlert wird bei >80% Auslastung erstellt"""
        # Customer hat 50 Lizenzen, 43 aktiv = 86%
        alert = LicenseAlert(
            customer_id=customer.id,
            alert_type="warning",
            message="Lizenzauslastung über 80%",
            threshold_percent=80,
            current_percent=86,
            acknowledged=False
        )
        db_session.add(alert)
        db_session.commit()

        assert alert.current_percent > alert.threshold_percent
```

```python
# apps/backend/tests/models/test_module.py

class TestModuleModels:

    def test_module_lifecycle(self, db_session, vendor_user):
        """AC-1.1.6: Module kann erstellt und released werden"""
        from app.models.module import Module, ModuleStatus
        from datetime import datetime

        module = Module(
            name="Checklist-Module",
            version="1.0.0",
            description="Checklisten für Prüfungen",
            status=ModuleStatus.development,
            developed_by=vendor_user.id
        )
        db_session.add(module)
        db_session.commit()

        assert module.status == ModuleStatus.development

        # Release
        module.status = ModuleStatus.released
        module.released_at = datetime.utcnow()
        db_session.commit()

        assert module.status == ModuleStatus.released
        assert module.released_at is not None

    def test_module_deployment_status(self, db_session, module, customer, vendor_user):
        """AC-1.1.7: ModuleDeployment tracked Status korrekt"""
        from app.models.module import ModuleDeployment, DeploymentStatus

        deployment = ModuleDeployment(
            module_id=module.id,
            customer_id=customer.id,
            status=DeploymentStatus.pending,
            deployed_version="1.0.0",
            deployed_by=vendor_user.id
        )
        db_session.add(deployment)
        db_session.commit()

        assert deployment.status == DeploymentStatus.pending

        # Deploy
        deployment.status = DeploymentStatus.deployed
        deployment.deployed_at = datetime.utcnow()
        db_session.commit()

        assert deployment.status == DeploymentStatus.deployed

    def test_release_note_creation(self, db_session, module):
        """AC-1.1.8: ReleaseNote wird bei Release erstellt"""
        from app.models.module import ReleaseNote

        note = ReleaseNote(
            module_id=module.id,
            version="1.0.0",
            title="Initial Release",
            changes=["Feature A hinzugefügt", "Feature B hinzugefügt"],
            breaking_changes=[],
            published_at=datetime.utcnow()
        )
        db_session.add(note)
        db_session.commit()

        assert len(note.changes) == 2
```

---

## 1.2 Datenbank-Migrationen

### Aufgaben

```
Dateien:
- apps/backend/alembic/versions/xxx_add_vendor_layer.py
- apps/backend/alembic/versions/xxx_add_customer_licensing.py
- apps/backend/alembic/versions/xxx_add_modules.py
```

- [ ] Migration: Vendor + VendorUser Tabellen
- [ ] Migration: Customer + LicenseUsage + LicenseAlert Tabellen
- [ ] Migration: Module + ModuleDeployment + ReleaseNote Tabellen
- [ ] Migration: VendorRole Enum zu bestehender User-Tabelle
- [ ] Fremdschlüssel-Constraints
- [ ] Indexes für häufige Queries

### Akzeptanzkriterien 1.2

| ID | Kriterium | Test |
|----|-----------|------|
| AC-1.2.1 | `alembic upgrade head` läuft ohne Fehler | `test_migration_upgrade` |
| AC-1.2.2 | `alembic downgrade -1` läuft ohne Fehler | `test_migration_downgrade` |
| AC-1.2.3 | Alle Tabellen sind erstellt | `test_tables_exist` |
| AC-1.2.4 | FK-Constraints funktionieren | `test_foreign_key_constraints` |

### Tests 1.2

```python
# apps/backend/tests/migrations/test_layer_migrations.py

def test_migration_upgrade(alembic_runner):
    """AC-1.2.1: Migration läuft ohne Fehler"""
    alembic_runner.migrate_up_to("head")

def test_tables_exist(db_session):
    """AC-1.2.3: Alle Tabellen sind erstellt"""
    from sqlalchemy import inspect
    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()

    expected_tables = [
        "vendors", "vendor_users",
        "customers", "license_usages", "license_alerts",
        "modules", "module_deployments", "release_notes"
    ]

    for table in expected_tables:
        assert table in tables, f"Table {table} not found"
```

---

## 1.3 Pydantic Schemas

### Aufgaben

```
Dateien:
- apps/backend/app/schemas/vendor.py (NEU)
- apps/backend/app/schemas/customer.py (NEU)
- apps/backend/app/schemas/module.py (NEU)
```

- [ ] VendorCreate, VendorUpdate, VendorResponse
- [ ] VendorUserCreate, VendorUserUpdate, VendorUserResponse
- [ ] CustomerCreate, CustomerUpdate, CustomerResponse
- [ ] CustomerWithLicenses (inkl. Usage + Alerts)
- [ ] LicenseUsageResponse, LicenseAlertResponse
- [ ] ModuleCreate, ModuleUpdate, ModuleResponse
- [ ] ModuleDeploymentCreate, ModuleDeploymentResponse
- [ ] ReleaseNoteCreate, ReleaseNoteResponse

### Akzeptanzkriterien 1.3

| ID | Kriterium | Test |
|----|-----------|------|
| AC-1.3.1 | Schemas validieren Eingaben korrekt | `test_schema_validation` |
| AC-1.3.2 | Fehlende Pflichtfelder werden abgelehnt | `test_required_fields` |
| AC-1.3.3 | Email-Format wird validiert | `test_email_validation` |
| AC-1.3.4 | Enum-Werte werden validiert | `test_enum_validation` |

---

## 1.4 API-Endpoints

### Aufgaben

```
Dateien:
- apps/backend/app/api/vendor.py (NEU)
- apps/backend/app/api/customers.py (NEU)
- apps/backend/app/api/modules.py (NEU)
- apps/backend/app/api/licenses.py (NEU)
```

#### Vendor-API
- [ ] `GET /api/v1/vendor` - Vendor-Infos (nur vendor_*)
- [ ] `PUT /api/v1/vendor` - Vendor aktualisieren (vendor_admin)
- [ ] `GET /api/v1/vendor/users` - Vendor-User auflisten
- [ ] `POST /api/v1/vendor/users` - Vendor-User erstellen (vendor_admin)
- [ ] `GET /api/v1/vendor/users/{id}` - Vendor-User Details
- [ ] `PUT /api/v1/vendor/users/{id}` - Vendor-User bearbeiten
- [ ] `DELETE /api/v1/vendor/users/{id}` - Vendor-User deaktivieren

#### Customers-API
- [ ] `GET /api/v1/customers` - Alle Kunden (vendor_*)
- [ ] `POST /api/v1/customers` - Neuen Kunden anlegen (vendor_admin)
- [ ] `GET /api/v1/customers/{id}` - Kunden-Details
- [ ] `PUT /api/v1/customers/{id}` - Kunden aktualisieren
- [ ] `DELETE /api/v1/customers/{id}` - Kunden deaktivieren (status=terminated)
- [ ] `GET /api/v1/customers/{id}/authorities` - Behörden des Kunden
- [ ] `GET /api/v1/customers/{id}/licenses` - Lizenz-Historie (30 Tage)
- [ ] `POST /api/v1/customers/{id}/licenses/adjust` - Lizenzen anpassen

#### Module-API
- [ ] `GET /api/v1/modules` - Alle Module
- [ ] `POST /api/v1/modules` - Neues Modul (vendor_developer)
- [ ] `GET /api/v1/modules/{id}` - Modul-Details
- [ ] `PUT /api/v1/modules/{id}` - Modul aktualisieren
- [ ] `POST /api/v1/modules/{id}/release` - Modul releasen (vendor_qa)
- [ ] `GET /api/v1/modules/{id}/deployments` - Alle Deployments
- [ ] `POST /api/v1/modules/{id}/deploy/{customer_id}` - An Kunden deployen
- [ ] `POST /api/v1/modules/{id}/rollback/{customer_id}` - Rollback

### Akzeptanzkriterien 1.4

| ID | Kriterium | Test |
|----|-----------|------|
| AC-1.4.1 | vendor_admin kann alle Endpoints aufrufen | `test_vendor_admin_access` |
| AC-1.4.2 | vendor_support hat nur Lesezugriff | `test_vendor_support_readonly` |
| AC-1.4.3 | vendor_developer kann Module erstellen | `test_developer_create_module` |
| AC-1.4.4 | vendor_qa kann Module releasen | `test_qa_release_module` |
| AC-1.4.5 | Normale User haben keinen Zugriff | `test_no_access_for_regular_users` |
| AC-1.4.6 | Customer-Erstellung erstellt Tenant automatisch | `test_customer_creates_tenant` |
| AC-1.4.7 | Lizenz-Historie zeigt 30 Tage | `test_license_history_30_days` |
| AC-1.4.8 | Deployment-Status wird korrekt aktualisiert | `test_deployment_status_update` |

### Tests 1.4

```python
# apps/backend/tests/api/test_vendor_api.py

import pytest
from httpx import AsyncClient

class TestVendorAPI:

    @pytest.mark.asyncio
    async def test_vendor_admin_access(self, client: AsyncClient, vendor_admin_token):
        """AC-1.4.1: vendor_admin kann alle Endpoints aufrufen"""
        headers = {"Authorization": f"Bearer {vendor_admin_token}"}

        # GET vendor
        response = await client.get("/api/v1/vendor", headers=headers)
        assert response.status_code == 200

        # GET customers
        response = await client.get("/api/v1/customers", headers=headers)
        assert response.status_code == 200

        # POST customer
        response = await client.post("/api/v1/customers", headers=headers, json={
            "contract_number": "2024-TEST-001",
            "licensed_users": 10,
            "licensed_authorities": 2,
            "tenant_name": "Test Kunde"
        })
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_vendor_support_readonly(self, client: AsyncClient, vendor_support_token):
        """AC-1.4.2: vendor_support hat nur Lesezugriff"""
        headers = {"Authorization": f"Bearer {vendor_support_token}"}

        # GET erlaubt
        response = await client.get("/api/v1/customers", headers=headers)
        assert response.status_code == 200

        # POST verboten
        response = await client.post("/api/v1/customers", headers=headers, json={
            "contract_number": "2024-TEST-002",
            "licensed_users": 10
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_developer_create_module(self, client: AsyncClient, vendor_developer_token):
        """AC-1.4.3: vendor_developer kann Module erstellen"""
        headers = {"Authorization": f"Bearer {vendor_developer_token}"}

        response = await client.post("/api/v1/modules", headers=headers, json={
            "name": "Test-Module",
            "version": "1.0.0",
            "description": "Test"
        })
        assert response.status_code == 201
        assert response.json()["status"] == "development"

    @pytest.mark.asyncio
    async def test_qa_release_module(self, client: AsyncClient, vendor_qa_token, module_id):
        """AC-1.4.4: vendor_qa kann Module releasen"""
        headers = {"Authorization": f"Bearer {vendor_qa_token}"}

        response = await client.post(f"/api/v1/modules/{module_id}/release", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "released"

    @pytest.mark.asyncio
    async def test_no_access_for_regular_users(self, client: AsyncClient, regular_user_token):
        """AC-1.4.5: Normale User haben keinen Zugriff"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        response = await client.get("/api/v1/vendor", headers=headers)
        assert response.status_code == 403

        response = await client.get("/api/v1/customers", headers=headers)
        assert response.status_code == 403
```

```python
# apps/backend/tests/api/test_customers_api.py

class TestCustomersAPI:

    @pytest.mark.asyncio
    async def test_customer_creates_tenant(self, client: AsyncClient, vendor_admin_token):
        """AC-1.4.6: Customer-Erstellung erstellt Tenant automatisch"""
        headers = {"Authorization": f"Bearer {vendor_admin_token}"}

        response = await client.post("/api/v1/customers", headers=headers, json={
            "contract_number": "2024-AUTO-001",
            "licensed_users": 50,
            "licensed_authorities": 5,
            "tenant_name": "Auto-Created Tenant",
            "tenant_type": "group"
        })
        assert response.status_code == 201

        data = response.json()
        assert data["tenant_id"] is not None

        # Verify tenant exists
        response = await client.get(f"/api/v1/tenants/{data['tenant_id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Auto-Created Tenant"

    @pytest.mark.asyncio
    async def test_license_history_30_days(self, client: AsyncClient, vendor_admin_token, customer_id):
        """AC-1.4.7: Lizenz-Historie zeigt 30 Tage"""
        headers = {"Authorization": f"Bearer {vendor_admin_token}"}

        response = await client.get(
            f"/api/v1/customers/{customer_id}/licenses",
            headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert len(data["history"]) <= 30
```

---

## 1.5 Frontend: Vendor-Portal

### Aufgaben

```
Dateien:
- apps/frontend/src/views/VendorDashboard.vue (NEU)
- apps/frontend/src/views/CustomerManagement.vue (NEU)
- apps/frontend/src/views/CustomerDetail.vue (NEU)
- apps/frontend/src/views/ModuleManagement.vue (NEU)
- apps/frontend/src/stores/vendor.ts (NEU)
- apps/frontend/src/api/vendor.ts (NEU)
```

#### Views
- [ ] `VendorDashboard.vue` - Übersicht (Kunden, Lizenzen, Module, Support)
- [ ] `CustomerManagement.vue` - Kunden-Liste mit CRUD
- [ ] `CustomerDetail.vue` - Kunden-Details, Lizenzen, Behörden
- [ ] `ModuleManagement.vue` - Module entwickeln, testen, deployen

#### Komponenten
- [ ] `CustomerCard.vue` - Kunden-Kachel
- [ ] `LicenseGauge.vue` - Lizenz-Auslastung (Radial Gauge)
- [ ] `LicenseChart.vue` - Lizenz-Verlauf (Line Chart)
- [ ] `ModuleCard.vue` - Modul-Karte mit Status
- [ ] `DeploymentTimeline.vue` - Deployment-Historie

#### Store
- [ ] `vendor.ts` Pinia Store
  - State: vendor, customers, modules, selectedCustomer
  - Actions: fetchCustomers, createCustomer, updateCustomer
  - Actions: fetchModules, createModule, deployModule

### Akzeptanzkriterien 1.5

| ID | Kriterium | Test |
|----|-----------|------|
| AC-1.5.1 | VendorDashboard zeigt alle Kunden | E2E: `vendor-dashboard.spec.ts` |
| AC-1.5.2 | Kunden können erstellt werden | E2E: `customer-crud.spec.ts` |
| AC-1.5.3 | Lizenz-Gauge zeigt korrekte Auslastung | E2E: `license-gauge.spec.ts` |
| AC-1.5.4 | Module können deployed werden | E2E: `module-deployment.spec.ts` |
| AC-1.5.5 | Nur vendor_* Rollen sehen das Portal | E2E: `vendor-access.spec.ts` |

### Tests 1.5

```typescript
// apps/frontend/tests/e2e/vendor-dashboard.spec.ts

import { test, expect } from '@playwright/test'

test.describe('Vendor Dashboard', () => {

  test.beforeEach(async ({ page }) => {
    // Login as vendor_admin
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'admin@flowaudit.de')
    await page.fill('[data-testid="password"]', 'password')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/vendor/dashboard')
  })

  test('AC-1.5.1: zeigt alle Kunden', async ({ page }) => {
    await expect(page.locator('[data-testid="customer-card"]')).toHaveCount.greaterThan(0)
  })

  test('AC-1.5.2: Kunde kann erstellt werden', async ({ page }) => {
    await page.click('[data-testid="add-customer"]')
    await page.fill('[data-testid="contract-number"]', '2024-E2E-001')
    await page.fill('[data-testid="tenant-name"]', 'E2E Test Kunde')
    await page.fill('[data-testid="licensed-users"]', '25')
    await page.click('[data-testid="save-customer"]')

    await expect(page.locator('text=E2E Test Kunde')).toBeVisible()
  })

  test('AC-1.5.3: Lizenz-Gauge zeigt Auslastung', async ({ page }) => {
    await page.click('[data-testid="customer-card"]').first()

    const gauge = page.locator('[data-testid="license-gauge"]')
    await expect(gauge).toBeVisible()
    await expect(gauge.locator('[data-testid="gauge-value"]')).toContainText('%')
  })

  test('AC-1.5.5: Normale User sehen Portal nicht', async ({ page }) => {
    // Logout
    await page.click('[data-testid="logout"]')

    // Login as regular user
    await page.fill('[data-testid="email"]', 'user@example.de')
    await page.fill('[data-testid="password"]', 'password')
    await page.click('[data-testid="login-button"]')

    // Should not see vendor dashboard
    await page.goto('/vendor/dashboard')
    await expect(page).toHaveURL('/dashboard') // Redirected
  })
})
```

---

# Feature 2: Layer 1 - Coordination Body (Konzern)

## 2.1 Backend-Modelle

### Aufgaben

```
Dateien:
- apps/backend/app/models/profile.py (NEU)
```

- [ ] `CoordinationBodyProfile` Model erstellen
  - id: UUID (PK)
  - tenant_id: UUID (FK → Tenant, unique)
  - official_name: str
  - short_name: str
  - street, postal_code, city, country
  - phone, email, website
  - logo_url: str | None
  - primary_color: str (hex)
  - secondary_color: str (hex)
  - created_at, updated_at

### Akzeptanzkriterien 2.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-2.1.1 | Profile kann für Tenant erstellt werden | `test_create_cb_profile` |
| AC-2.1.2 | Logo kann hochgeladen werden | `test_upload_logo` |
| AC-2.1.3 | Farben werden validiert (hex) | `test_color_validation` |

---

## 2.2 API-Endpoints

### Aufgaben

```
Dateien:
- apps/backend/app/api/profiles.py (NEU)
```

- [ ] `GET /api/v1/tenants/{id}/profile` - Profil abrufen
- [ ] `PUT /api/v1/tenants/{id}/profile` - Profil aktualisieren
- [ ] `POST /api/v1/tenants/{id}/profile/logo` - Logo hochladen (multipart)

### Akzeptanzkriterien 2.2

| ID | Kriterium | Test |
|----|-----------|------|
| AC-2.2.1 | group_admin kann eigenes Profil bearbeiten | `test_group_admin_edit_profile` |
| AC-2.2.2 | group_admin kann fremdes Profil NICHT bearbeiten | `test_group_admin_no_cross_edit` |
| AC-2.2.3 | vendor_admin kann alle Profile bearbeiten | `test_vendor_admin_all_profiles` |
| AC-2.2.4 | Logo-Upload akzeptiert nur Bilder | `test_logo_upload_validation` |

---

## 2.3 Frontend: CB-Admin-Portal

### Aufgaben

```
Dateien:
- apps/frontend/src/views/TenantAdmin.vue (NEU)
- apps/frontend/src/components/admin/ProfileEditor.vue (NEU)
- apps/frontend/src/components/admin/AuthorityList.vue (NEU)
- apps/frontend/src/components/admin/UserManager.vue (NEU)
- apps/frontend/src/components/admin/LicenseAllocation.vue (NEU)
```

#### TenantAdmin.vue Tabs
- [ ] Tab 1: Prüfbehörden - AuthorityList.vue
- [ ] Tab 2: Benutzer - UserManager.vue
- [ ] Tab 3: Templates - TenantTemplates.vue
- [ ] Tab 4: Stammdaten - ProfileEditor.vue
- [ ] Tab 5: Lizenzen - LicenseAllocation.vue

### Akzeptanzkriterien 2.3

| ID | Kriterium | Test |
|----|-----------|------|
| AC-2.3.1 | group_admin sieht alle Tabs | E2E: `tenant-admin.spec.ts` |
| AC-2.3.2 | Prüfbehörden können angelegt werden | E2E |
| AC-2.3.3 | Benutzer können verwaltet werden | E2E |
| AC-2.3.4 | Stammdaten können bearbeitet werden | E2E |
| AC-2.3.5 | Lizenzen können an Behörden verteilt werden | E2E |

---

# Feature 3: Layer 2 - Prüfbehörde Admin

## 3.1 Backend-Modelle

### Aufgaben

- [ ] `AuthorityProfile` Model in profile.py ergänzen
  - id: UUID (PK)
  - tenant_id: UUID (FK → Tenant, unique)
  - official_name, short_name, authority_type
  - Adresse, Kontakt
  - logo_url, use_parent_branding: bool
  - primary_color, secondary_color (optional, überschreibt CB)

### Akzeptanzkriterien 3.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-3.1.1 | AuthorityProfile erbt Branding von CB | `test_authority_inherits_branding` |
| AC-3.1.2 | Authority kann eigenes Branding setzen | `test_authority_custom_branding` |

---

## 3.2 Frontend: Authority-Admin

### Aufgaben

```
Dateien:
- apps/frontend/src/views/AuthorityAdmin.vue (NEU)
- apps/frontend/src/components/admin/TeamManager.vue (NEU)
```

#### Tabs
- [ ] Tab 1: Benutzer - UserManager.vue
- [ ] Tab 2: Teams - TeamManager.vue
- [ ] Tab 3: Templates - AuthorityTemplates.vue
- [ ] Tab 4: Stammdaten - ProfileEditor.vue

### Akzeptanzkriterien 3.2

| ID | Kriterium | Test |
|----|-----------|------|
| AC-3.2.1 | authority_head sieht alle Tabs | E2E |
| AC-3.2.2 | authority_head sieht nur eigene Behörde | E2E |
| AC-3.2.3 | Teams können erstellt werden | E2E |

---

# Feature 4: Layer-Dashboard

## 4.1 Backend-API

### Aufgaben

```
Dateien:
- apps/backend/app/api/dashboard.py (erweitern)
- apps/backend/app/schemas/dashboard.py (NEU)
```

- [ ] `GET /api/v1/dashboard/layers` - Hierarchie-Übersicht
- [ ] `GET /api/v1/dashboard/layers/{customer_id}` - Kunden-Detail
- [ ] `GET /api/v1/dashboard/layers/{customer_id}/authorities/{id}` - Behörden-Detail

#### Response-Schema
```python
class LayerDashboardResponse(BaseModel):
    vendor: VendorSummary
    total_customers: int
    total_licenses: int
    total_users: int
    customers: list[CustomerSummary]

class CustomerSummary(BaseModel):
    id: UUID
    name: str
    licensed_users: int
    active_users: int
    license_percent: float
    authority_count: int
    status: CustomerStatus
    authorities: list[AuthoritySummary] | None  # Optional, bei Drill-Down

class AuthoritySummary(BaseModel):
    id: UUID
    name: str
    user_count: int
    active_cases: int
    authority_head: str | None
```

### Akzeptanzkriterien 4.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-4.1.1 | vendor_admin sieht alle Kunden | `test_vendor_sees_all` |
| AC-4.1.2 | group_admin sieht nur eigenen Kunden | `test_group_admin_sees_own` |
| AC-4.1.3 | authority_head sieht nur eigene Behörde | `test_authority_sees_own` |
| AC-4.1.4 | Drill-Down zeigt Behörden-Details | `test_drill_down_authorities` |
| AC-4.1.5 | Lizenz-Prozent wird korrekt berechnet | `test_license_percent_calculation` |

### Tests 4.1

```python
# apps/backend/tests/api/test_dashboard_layers.py

class TestLayerDashboardAPI:

    @pytest.mark.asyncio
    async def test_vendor_sees_all(self, client, vendor_admin_token, test_customers):
        """AC-4.1.1: vendor_admin sieht alle Kunden"""
        headers = {"Authorization": f"Bearer {vendor_admin_token}"}

        response = await client.get("/api/v1/dashboard/layers", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total_customers"] == len(test_customers)
        assert len(data["customers"]) == len(test_customers)

    @pytest.mark.asyncio
    async def test_group_admin_sees_own(self, client, group_admin_token, test_customer):
        """AC-4.1.2: group_admin sieht nur eigenen Kunden"""
        headers = {"Authorization": f"Bearer {group_admin_token}"}

        response = await client.get("/api/v1/dashboard/layers", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["customers"]) == 1
        assert data["customers"][0]["id"] == str(test_customer.id)

    @pytest.mark.asyncio
    async def test_license_percent_calculation(self, client, vendor_admin_token, customer_50_43):
        """AC-4.1.5: Lizenz-Prozent wird korrekt berechnet"""
        # customer_50_43 hat 50 Lizenzen, 43 aktiv = 86%
        headers = {"Authorization": f"Bearer {vendor_admin_token}"}

        response = await client.get("/api/v1/dashboard/layers", headers=headers)
        data = response.json()

        customer = next(c for c in data["customers"] if c["id"] == str(customer_50_43.id))
        assert customer["license_percent"] == 86.0
```

---

## 4.2 Frontend: Layer-Dashboard

### Aufgaben

```
Dateien:
- apps/frontend/src/views/LayerDashboard.vue (NEU)
- apps/frontend/src/components/dashboard/LayerTree.vue (NEU)
- apps/frontend/src/components/dashboard/VendorCard.vue (NEU)
- apps/frontend/src/components/dashboard/CustomerCard.vue (NEU)
- apps/frontend/src/components/dashboard/AuthorityNode.vue (NEU)
- apps/frontend/src/components/dashboard/StatsCard.vue (NEU)
- apps/frontend/src/components/dashboard/StatusBadge.vue (NEU)
- apps/frontend/src/stores/layerDashboard.ts (NEU)
```

#### LayerDashboard.vue
- [ ] Vendor-Übersicht oben (Stats: Kunden, Lizenzen, Module)
- [ ] Kunden-Grid darunter (CustomerCard)
- [ ] Expand/Collapse für Behörden
- [ ] Detail-Panel (Sidebar) bei Selektion
- [ ] Drill-Down Navigation

#### LayerTree.vue
- [ ] Interaktiver Hierarchie-Baum
- [ ] Animate Expand/Collapse
- [ ] Connection Lines
- [ ] Zoom Controls

### Akzeptanzkriterien 4.2

| ID | Kriterium | Test |
|----|-----------|------|
| AC-4.2.1 | Dashboard lädt und zeigt Daten | E2E: `layer-dashboard.spec.ts` |
| AC-4.2.2 | Kunden können expandiert werden | E2E |
| AC-4.2.3 | Behörden werden bei Expand angezeigt | E2E |
| AC-4.2.4 | Klick auf Kunde öffnet Detail | E2E |
| AC-4.2.5 | Status-Badge zeigt korrekten Status | E2E |

### Tests 4.2

```typescript
// apps/frontend/tests/e2e/layer-dashboard.spec.ts

test.describe('Layer Dashboard', () => {

  test('AC-4.2.1: Dashboard lädt und zeigt Daten', async ({ page }) => {
    await page.goto('/admin/dashboard')

    // Vendor Stats
    await expect(page.locator('[data-testid="vendor-stats"]')).toBeVisible()

    // Customer Cards
    await expect(page.locator('[data-testid="customer-card"]')).toHaveCount.greaterThan(0)
  })

  test('AC-4.2.2: Kunden können expandiert werden', async ({ page }) => {
    await page.goto('/admin/dashboard')

    const customerCard = page.locator('[data-testid="customer-card"]').first()
    await customerCard.locator('[data-testid="expand-button"]').click()

    await expect(customerCard.locator('[data-testid="authority-node"]')).toBeVisible()
  })

  test('AC-4.2.5: Status-Badge zeigt korrekten Status', async ({ page }) => {
    await page.goto('/admin/dashboard')

    const activeBadge = page.locator('[data-testid="status-badge"][data-status="active"]')
    await expect(activeBadge).toContainText('Aktiv')
  })
})
```

---

# Feature 5: UI Enhancements

## 5.1 Shimmer Loader

### Aufgaben

```
Dateien:
- apps/frontend/src/styles/themes.css (erweitern)
- apps/frontend/src/components/common/SkeletonLoader.vue (NEU)
- apps/frontend/src/components/common/SkeletonTable.vue (NEU)
- apps/frontend/src/components/common/SkeletonCard.vue (NEU)
- apps/frontend/src/components/common/SkeletonStats.vue (NEU)
```

#### CSS
- [ ] `@keyframes shimmer`
- [ ] `@keyframes pulse-subtle`
- [ ] `@keyframes skeleton-wave`
- [ ] `.skeleton`, `.skeleton-text`, `.skeleton-avatar`, `.skeleton-card`
- [ ] `@media (prefers-reduced-motion)` - Accessibility

#### Komponenten
- [ ] `SkeletonLoader.vue` - Basis (type, size, variant, count props)
- [ ] `SkeletonTable.vue` - Tabellen-Skeleton
- [ ] `SkeletonCard.vue` - Karten-Skeleton
- [ ] `SkeletonStats.vue` - Dashboard-Stats

### Akzeptanzkriterien 5.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-5.1.1 | Skeleton wird während Laden angezeigt | E2E |
| AC-5.1.2 | Skeleton verschwindet nach Laden | E2E |
| AC-5.1.3 | Animation respektiert prefers-reduced-motion | Unit |
| AC-5.1.4 | Delayed Skeleton (200ms) funktioniert | E2E |

---

## 5.2 Microinteractions

### Aufgaben

```
Dateien:
- apps/frontend/src/composables/useRipple.ts (NEU)
- apps/frontend/src/composables/useButtonState.ts (NEU)
- apps/frontend/src/composables/useToast.ts (NEU)
- apps/frontend/src/components/common/EnhancedButton.vue (NEU)
- apps/frontend/src/components/common/ValidatedInput.vue (NEU)
- apps/frontend/src/components/common/Toast.vue (NEU)
- apps/frontend/src/components/common/ToastContainer.vue (NEU)
- apps/frontend/src/components/common/CopyButton.vue (NEU)
```

### Akzeptanzkriterien 5.2

| ID | Kriterium | Test |
|----|-----------|------|
| AC-5.2.1 | Ripple-Effekt bei Button-Klick | E2E |
| AC-5.2.2 | Button zeigt Success-State | E2E |
| AC-5.2.3 | Button zeigt Error-State mit Shake | E2E |
| AC-5.2.4 | Toast wird angezeigt und verschwindet | E2E |
| AC-5.2.5 | CopyButton kopiert und zeigt Bestätigung | E2E |

---

## 5.3 Radial View ✅ FERTIG

> Bereits implementiert: `apps/frontend/src/components/views/RadialView.vue`

---

## 5.4 View-Switcher Dropdown

### Aufgaben

```
Dateien:
- apps/frontend/src/components/common/ViewSwitcher.vue (NEU)
```

- [ ] Dropdown für 5 Views (Tiles, List, Tree, Radial, Minimal)
- [ ] Icon + Label pro Option
- [ ] Keyboard-Navigation (Arrow, Enter, Escape)
- [ ] LocalStorage pro Route
- [ ] Integration in DashboardView, AuditCasesView, GroupQueriesView

### Akzeptanzkriterien 5.4

| ID | Kriterium | Test |
|----|-----------|------|
| AC-5.4.1 | Dropdown zeigt alle 5 Views | E2E |
| AC-5.4.2 | View-Wechsel funktioniert | E2E |
| AC-5.4.3 | Auswahl wird in LocalStorage gespeichert | E2E |
| AC-5.4.4 | Keyboard-Navigation funktioniert | E2E |

---

# Feature 6: Modul-Distribution-System

## 6.1 Backend

### Aufgaben

```
Dateien:
- apps/backend/app/core/module_manager.py (NEU)
- modules/vp_ai/module.json (NEU)
```

- [ ] `module.json` Schema definieren
- [ ] `ModuleManager` Klasse
  - list_installed()
  - get_available()
  - install_module(id, version)
  - update_module(id)
  - uninstall_module(id)

### Akzeptanzkriterien 6.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-6.1.1 | Module können installiert werden | `test_install_module` |
| AC-6.1.2 | Module können aktualisiert werden | `test_update_module` |
| AC-6.1.3 | Module können deinstalliert werden | `test_uninstall_module` |
| AC-6.1.4 | Abhängigkeiten werden geprüft | `test_dependency_check` |

---

# Feature 7: Workflow-Historisierung

## 7.1 Backend-Modelle

### Aufgaben

```
Dateien:
- apps/backend/app/models/history.py (NEU)
- apps/backend/app/services/context_service.py (NEU)
```

- [ ] `ModuleEvent` - Events in Modul-Geschichte
- [ ] `LLMConversation` - LLM-Sessions
- [ ] `LLMMessage` - Nachrichten
- [ ] `LLMFeedback` - User-Feedback
- [ ] `ContextService` - Kontext-Aufbau für LLM

### Akzeptanzkriterien 7.1

| ID | Kriterium | Test |
|----|-----------|------|
| AC-7.1.1 | Events werden geloggt | `test_event_logging` |
| AC-7.1.2 | Konversationen werden gespeichert | `test_conversation_storage` |
| AC-7.1.3 | Feedback kann hinzugefügt werden | `test_feedback_addition` |
| AC-7.1.4 | Kontext wird korrekt aufgebaut | `test_context_building` |

---

# Gap-Analyse Status

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

# Claude CLI Befehle

## 1. Layer 0 starten:
```
Implementiere Feature 1 (Layer 0: Vendor & Development Module) basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md.

Beginne mit Abschnitt 1.1 (Backend-Modelle):
1. Erstelle apps/backend/app/models/vendor.py mit Vendor und VendorUser
2. Erstelle apps/backend/app/models/customer.py mit Customer, LicenseUsage, LicenseAlert
3. Erweitere VendorRole Enum in user.py
4. Erstelle Alembic-Migration

Stelle sicher, dass alle Akzeptanzkriterien AC-1.1.* erfüllt sind.
Schreibe die Tests aus Abschnitt "Tests 1.1".
```

## 2. Layer-Dashboard starten:
```
Implementiere Feature 4 (Layer-Dashboard) basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md.

Beginne mit Abschnitt 4.1 (Backend-API):
1. Erweitere apps/backend/app/api/dashboard.py
2. Erstelle LayerDashboardResponse Schema
3. Implementiere Berechtigungsprüfung

Stelle sicher, dass alle Akzeptanzkriterien AC-4.1.* erfüllt sind.
Schreibe die Tests aus Abschnitt "Tests 4.1".
```

## 3. UI Enhancements starten:
```
Implementiere Feature 5 (UI Enhancements) basierend auf
docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md.

Beginne mit Abschnitt 5.1 (Shimmer Loader):
1. Erweitere apps/frontend/src/styles/themes.css mit Skeleton-Animationen
2. Erstelle SkeletonLoader.vue, SkeletonTable.vue, SkeletonCard.vue
3. Integriere in AuditCasesView.vue

Stelle sicher, dass alle Akzeptanzkriterien AC-5.1.* erfüllt sind.
```

---

# Test-Ausführung

## Backend-Tests
```bash
cd apps/backend
pytest tests/ -v --cov=app --cov-report=html
```

## Frontend-Tests
```bash
cd apps/frontend
pnpm test:unit
pnpm test:e2e
```

## Alle Tests
```bash
# Root
./scripts/test-all.sh
```

---

*Dokumentation basiert auf: LAYER-STRUKTUR.md, 02_IMPLEMENTATION_TASKS.md*
*Erstellt für Claude CLI Implementierung*
