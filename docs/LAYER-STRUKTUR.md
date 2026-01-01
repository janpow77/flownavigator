# FlowNavigator Layer-Struktur und Rollen

---

## Layer 0: Vendor (Softwarefirma)

Die oberste Ebene ist der **Vendor** (Softwarefirma), der das gesamte System betreibt und alle Kunden (Coordination Bodies) verwaltet.

### Vendor-Hierarchie

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LAYER 0: VENDOR                                  │
│                     (Softwarefirma/Betreiber)                           │
│                                                                         │
│  Rollen: vendor_admin, vendor_support                                   │
│                                                                         │
│  Verwaltung:                                                            │
│  • Kunden (Coordination Bodies)                                         │
│  • Lizenzen & Abrechnung                                                │
│  • Globale Templates                                                    │
│  • System-Konfiguration                                                 │
│  • Support-Zugang                                                       │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   KUNDE A     │       │   KUNDE B     │       │   KUNDE C     │
│ (Coord. Body) │       │ (Coord. Body) │       │ (Coord. Body) │
│               │       │               │       │               │
│ 50 Lizenzen   │       │ 200 Lizenzen  │       │ 25 Lizenzen   │
│ 43 aktiv      │       │ 187 aktiv     │       │ 22 aktiv      │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Vendor-Rollen (NEU)

| Rolle | Beschreibung | Befugnisse |
|-------|--------------|------------|
| `vendor_admin` | Vendor-Administrator | Alle Kunden, Lizenzen, globale Einstellungen |
| `vendor_support` | Support-Mitarbeiter | Lesezugriff auf Kundendaten für Support |

### Vendor-Datenmodell

```python
class Vendor(Base):
    """Softwarefirma/Betreiber des Systems."""
    id: UUID
    name: str                          # "FlowAudit GmbH"
    contact_email: str                 # "support@flowaudit.de"
    billing_email: str                 # "billing@flowaudit.de"
    address: Address                   # Firmenadresse

class VendorUser(Base):
    """Mitarbeiter der Softwarefirma."""
    id: UUID
    vendor_id: UUID
    email: str
    role: "vendor_admin" | "vendor_support"

class Customer(Base):
    """Kunde = Coordination Body mit Lizenzvertrag."""
    id: UUID
    tenant_id: UUID                    # Verknüpfung zum Tenant

    # Vertragsdaten
    contract_number: str               # "2024-CB-001"
    contract_start: date
    contract_end: date | None

    # Lizenzen
    licensed_users: int                # Gekaufte Lizenzen
    licensed_authorities: int          # Max. Prüfbehörden

    # Abrechnung
    billing_contact: str
    billing_address: Address
    payment_method: str

    # Status
    status: "active" | "suspended" | "trial" | "terminated"
```

### Lizenz-Dashboard (Vendor-Sicht)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  KUNDEN-ÜBERSICHT                                          [+ Neuer Kunde]
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Kunde: EU-Prüfungskoordination                    Status: ✅ Aktiv │
│  │ Vertrag: 2024-CB-001 (01.01.2024 - 31.12.2026)                   │
│  │                                                                   │
│  │ Lizenzen:  50 gekauft │ 43 aktiv │ 7 verfügbar │ ⚠️ 86% genutzt  │
│  │ Behörden:   5 erlaubt │  3 aktiv │ 2 verfügbar                   │
│  │                                                                   │
│  │ [Bearbeiten] [Lizenzen erweitern] [Support-Zugang] [Deaktivieren]│
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Kunde: Bundesländer-Verbund                       Status: ✅ Aktiv │
│  │ Vertrag: 2023-CB-002 (01.07.2023 - 30.06.2025)                   │
│  │                                                                   │
│  │ Lizenzen: 200 gekauft │ 187 aktiv │ 13 verfügbar │ 94% genutzt   │
│  │ Behörden:  16 erlaubt │  14 aktiv │  2 verfügbar                 │
│  │                                                                   │
│  │ [Bearbeiten] [Lizenzen erweitern] [Support-Zugang] [Deaktivieren]│
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Administrations-Konzept (alle Layer)

### Übersicht: Was wird auf welchem Layer administriert?

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 0: VENDOR (Softwarefirma)                                         │
│ ────────────────────────────────────────────────────────────────────────│
│ • Kunden anlegen/verwalten (Coordination Bodies)                        │
│ • Lizenzverträge & Kontingente                                          │
│ • Globale Templates (Basis-Checklisten, Standard-Workflows)             │
│ • Systemweite Konfiguration                                             │
│ • Support-Zugänge                                                       │
│ • Abrechnungsdaten                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: COORDINATION BODY (Konzern)                                    │
│ ────────────────────────────────────────────────────────────────────────│
│ • Prüfbehörden anlegen/verwalten                                        │
│ • Benutzer im Konzern verwalten                                         │
│ • Konzern-Templates (überschreiben globale Templates)                   │
│ • Konzern-Stammdaten (Name, Adresse, Logo)                              │
│ • Lizenzkontingent auf Behörden verteilen                               │
│ • Konzern-weite Einstellungen                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: PRÜFBEHÖRDE (Authority)                                        │
│ ────────────────────────────────────────────────────────────────────────│
│ • Benutzer in der Behörde verwalten                                     │
│ • Behörden-Templates (überschreiben Konzern-Templates)                  │
│ • Behörden-Stammdaten (Name, Adresse, Logo)                             │
│ • Prüfteams konfigurieren                                               │
│ • Behörden-spezifische Einstellungen                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Template-Hierarchie (Vererbung)

Templates werden hierarchisch vererbt und können auf jeder Ebene überschrieben werden:

```
VENDOR (Globale Templates)
    │
    │  Basis-Checklisten, Standard-Workflows, Default-Einstellungen
    │
    ▼
COORDINATION BODY (Konzern-Templates)
    │
    │  Erbt von Vendor, kann anpassen/erweitern
    │  z.B. EU-spezifische Prüfkriterien
    │
    ▼
PRÜFBEHÖRDE (Behörden-Templates)
    │
    │  Erbt von Konzern, kann anpassen/erweitern
    │  z.B. Landesspezifische Anforderungen
    │
    ▼
PRÜFFALL (Instanz)

    Verwendet das effektive Template der Behörde
```

### Template-Typen

| Template-Typ | Beschreibung | Beispiel |
|--------------|--------------|----------|
| **Checklisten** | Prüfschritte und Kriterien | "EU-Fördermittel Vor-Ort-Prüfung" |
| **Workflows** | Ablauf von Prüfungen | "Standard-Prüfungsprozess 4-Augen" |
| **Dokument-Vorlagen** | Brief- und Berichtvorlagen | "Prüfbericht-Vorlage.docx" |
| **Findings-Kategorien** | Kategorisierung von Feststellungen | "Finanziell", "Verfahren", "Compliance" |
| **Berechnungsregeln** | Fehlerquoten, Stichproben | "Stichprobenberechnung nach EU-VO" |

### Template-Datenmodell

```python
class Template(Base):
    id: UUID
    type: "checklist" | "workflow" | "document" | "finding_category" | "calculation"
    name: str
    version: str                       # "1.0.0"

    # Hierarchie
    scope: "vendor" | "group" | "authority"
    owner_id: UUID                     # Vendor, Tenant (group), oder Tenant (authority)
    parent_template_id: UUID | None    # Überschreibt dieses Template

    # Inhalt
    content: dict                      # JSONB - Template-spezifische Daten

    # Status
    status: "draft" | "active" | "deprecated"
    is_default: bool                   # Standard-Template für neue Entities
```

---

## Stammdaten-Verwaltung

### Auf Layer 0 (Vendor)

```python
class VendorSettings(Base):
    """Globale System-Einstellungen."""
    id: UUID

    # Branding
    system_name: str                   # "FlowAudit"
    logo_url: str
    primary_color: str                 # "#1E40AF"

    # Defaults
    default_language: str              # "de"
    default_timezone: str              # "Europe/Berlin"

    # Features
    enabled_modules: list[str]         # ["checklists", "findings", "documents"]
    max_file_upload_size_mb: int       # 50
```

### Auf Layer 1 (Coordination Body)

```python
class CoordinationBodyProfile(Base):
    """Stammdaten eines Coordination Body."""
    tenant_id: UUID                    # FK zu Tenant

    # Grunddaten
    official_name: str                 # "Europäische Prüfungskoordination"
    short_name: str                    # "EU-PK"
    legal_form: str                    # "Körperschaft des öffentlichen Rechts"

    # Adresse
    street: str
    postal_code: str
    city: str
    country: str

    # Kontakt
    phone: str
    email: str
    website: str

    # Branding
    logo_url: str
    primary_color: str
    secondary_color: str

    # Rechnungsadresse (falls abweichend)
    billing_address: Address | None
    billing_contact: str
```

### Auf Layer 2 (Prüfbehörde)

```python
class AuthorityProfile(Base):
    """Stammdaten einer Prüfbehörde."""
    tenant_id: UUID                    # FK zu Tenant

    # Grunddaten
    official_name: str                 # "Bundesrechnungshof"
    short_name: str                    # "BRH"
    authority_type: str                # "Oberste Bundesbehörde"

    # Adresse
    street: str
    postal_code: str
    city: str
    state: str                         # Bundesland
    country: str

    # Kontakt
    phone: str
    fax: str
    email: str
    website: str

    # Leitung
    head_title: str                    # "Präsident"
    head_name: str                     # "Dr. Max Mustermann"

    # Branding (überschreibt Konzern)
    logo_url: str | None
    use_parent_branding: bool          # True = Konzern-Branding verwenden
```

---

## Benutzer-Administration

### Benutzer-Verwaltung pro Layer

| Layer | Wer verwaltet? | Was kann verwaltet werden? |
|-------|----------------|---------------------------|
| **Vendor** | `vendor_admin` | Vendor-Mitarbeiter, Support-Zugänge |
| **Coord. Body** | `group_admin` | Alle Benutzer im Konzern + Behörden |
| **Prüfbehörde** | `authority_head` | Nur Benutzer in der eigenen Behörde |

### Benutzer-Datenmodell (erweitert)

```python
class User(Base):
    id: UUID
    tenant_id: UUID

    # Persönliche Daten
    email: str
    first_name: str
    last_name: str
    title: str | None                  # "Dr.", "Prof."

    # Rolle
    role: UserRole

    # Kontakt
    phone: str | None
    mobile: str | None
    office_location: str | None        # "Raum 4.12"

    # Signatur (für Berichte)
    signature_title: str | None        # "Oberamtsrat"
    signature_department: str | None   # "Abteilung III/2"

    # Status
    is_active: bool
    last_login_at: datetime | None
    password_changed_at: datetime | None
    must_change_password: bool
```

### Lizenz-Tracking

```python
class LicenseUsage(Base):
    """Tracking der Lizenznutzung."""
    customer_id: UUID                  # FK zu Customer

    # Aktueller Stand
    active_users: int                  # Aktive Benutzer (is_active=True)
    licensed_users: int                # Gekaufte Lizenzen

    # Historie
    date: date
    peak_users: int                    # Maximum an diesem Tag

class LicenseAlert(Base):
    """Warnungen bei Lizenzüberschreitung."""
    customer_id: UUID
    alert_type: "warning_80" | "warning_90" | "exceeded"
    triggered_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: UUID | None       # Vendor-User
```

---

## Administrations-UI pro Layer

### Layer 0: Vendor-Admin-Portal

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VENDOR ADMIN PORTAL                                    [Admin: J.Schmidt]
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Kunden   │ │ Lizenzen │ │Templates │ │ Support  │ │ System   │      │
│  │    12    │ │  475/500 │ │    24    │ │  3 offen │ │ Settings │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                                         │
│  SCHNELLZUGRIFF                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│  [+ Neuer Kunde]  [+ Globales Template]  [Lizenz-Report]  [Audit-Log]  │
│                                                                         │
│  KUNDEN MIT LIZENZWARNUNG                                               │
│  ─────────────────────────────────────────────────────────────────────  │
│  ⚠️ Bundesländer-Verbund: 94% Lizenzauslastung (187/200)               │
│  ⚠️ Bayern-Prüfung e.V.: 88% Lizenzauslastung (44/50)                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Coordination Body Admin

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EU-PRÜFUNGSKOORDINATION - ADMINISTRATION              [Admin: M.Müller]
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ Prüfbehörden │ │   Benutzer   │ │  Templates   │ │ Stammdaten   │   │
│  │      3       │ │    43/50     │ │     12       │ │  [Bearbeiten]│   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                         │
│  PRÜFBEHÖRDEN                                                           │
│  ─────────────────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Bundesrechnungshof                              15 Benutzer     │   │
│  │ Adresse: Adenauerallee 81, 53113 Bonn          [Bearbeiten]     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Landesrechnungshof Bayern                       12 Benutzer     │   │
│  │ Adresse: Arcisstraße 1, 80333 München          [Bearbeiten]     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [+ Neue Prüfbehörde]                                                   │
│                                                                         │
│  BENUTZER IM KONZERN                                                    │
│  ─────────────────────────────────────────────────────────────────────  │
│  │ Name              │ Rolle          │ Behörde        │ Status │      │
│  │───────────────────│────────────────│────────────────│────────│      │
│  │ Max Müller        │ group_admin    │ Koordination   │ ✅     │      │
│  │ Anna Schmidt      │ authority_head │ Koordination   │ ✅     │      │
│  │ Sabine Meier      │ authority_head │ BRH            │ ✅     │      │
│  │ Klaus Fischer     │ team_leader    │ BRH            │ ✅     │      │
│  │ ...               │                │                │        │      │
│                                                                         │
│  [+ Neuer Benutzer]  [Benutzer importieren]  [Inaktive anzeigen]       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer 2: Prüfbehörden-Admin

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BUNDESRECHNUNGSHOF - ADMINISTRATION                  [Admin: S.Meier] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │   Benutzer   │ │  Templates   │ │ Stammdaten   │ │    Teams     │   │
│  │     15       │ │      5       │ │ [Bearbeiten] │ │      3       │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                                         │
│  STAMMDATEN                                                             │
│  ─────────────────────────────────────────────────────────────────────  │
│  Name:      Bundesrechnungshof                                          │
│  Kurzname:  BRH                                                         │
│  Adresse:   Adenauerallee 81, 53113 Bonn                               │
│  Telefon:   +49 228 99-5001                                            │
│  E-Mail:    poststelle@brh.bund.de                                     │
│  Website:   www.bundesrechnungshof.de                                  │
│  Leitung:   Präsident Dr. Kay Scheller                                 │
│                                                                [Bearbeiten]
│                                                                         │
│  BENUTZER                                                               │
│  ─────────────────────────────────────────────────────────────────────  │
│  │ Name              │ Rolle          │ Team           │ Status │      │
│  │───────────────────│────────────────│────────────────│────────│      │
│  │ Sabine Meier      │ authority_head │ -              │ ✅     │      │
│  │ Klaus Fischer     │ team_leader    │ Team A         │ ✅     │      │
│  │ Julia Bauer       │ auditor        │ Team A         │ ✅     │      │
│  │ Michael Wolf      │ viewer         │ -              │ ✅     │      │
│  │ ...               │                │                │        │      │
│                                                                         │
│  [+ Neuer Benutzer]  (Lizenzinfo: 15 von 20 Plätzen belegt)            │
│                                                                         │
│  BEHÖRDEN-TEMPLATES (überschreiben Konzern-Templates)                   │
│  ─────────────────────────────────────────────────────────────────────  │
│  │ Template                        │ Basis           │ Status │        │
│  │─────────────────────────────────│─────────────────│────────│        │
│  │ BRH-Checkliste Vor-Ort         │ EU-Standard     │ Aktiv  │        │
│  │ BRH-Berichtvorlage             │ EU-Standard     │ Aktiv  │        │
│  │ BRH-Findings-Kategorien        │ (eigene)        │ Aktiv  │        │
│                                                                         │
│  [+ Neues Template]  [Konzern-Template überschreiben]                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

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

---

## Layer 0: Development Module

Auf Layer 0 (Vendor) befindet sich auch das **Development Module** für die Softwareentwicklung und -wartung.

### Development-Funktionen

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 0: DEVELOPMENT MODULE                                             │
│ ────────────────────────────────────────────────────────────────────────│
│                                                                         │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│ │  MODUL-         │  │  TEMPLATE-      │  │  DEPLOYMENT-    │          │
│ │  ENTWICKLUNG    │  │  ENTWICKLUNG    │  │  MANAGEMENT     │          │
│ └────────┬────────┘  └────────┬────────┘  └────────┬────────┘          │
│          │                    │                    │                    │
│          ▼                    ▼                    ▼                    │
│  • Neue Module           • Basis-Templates    • Release-Planung        │
│  • LLM-Konfiguration     • Checklisten        • Rollout an Kunden      │
│  • API-Erweiterungen     • Workflows          • Versionsmanagement     │
│  • Feature-Flags         • Berechnungen       • Hotfix-Deployment      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Development-Rollen (erweitert)

| Rolle | Beschreibung | Befugnisse |
|-------|--------------|------------|
| `vendor_admin` | Vendor-Administrator | Alles inkl. Development |
| `vendor_support` | Support-Mitarbeiter | Lesezugriff, Tickets |
| `vendor_developer` | Entwickler | Module, Templates, Code |
| `vendor_qa` | Quality Assurance | Testing, Freigabe |

### Development-Datenmodelle

```python
class Module(Base):
    """Software-Modul das an Kunden verteilt werden kann."""
    id: UUID
    name: str                          # "Checklist-Module"
    version: str                       # "2.1.0"
    description: str

    # Entwicklung
    status: "development" | "testing" | "released" | "deprecated"
    developed_by: UUID                 # VendorUser
    released_at: datetime | None

    # Abhängigkeiten
    dependencies: list[str]            # ["core", "auth"]
    min_system_version: str            # "1.5.0"

    # Feature-Flags
    feature_flags: dict                # {"new_ui": true, "beta_feature": false}

class ModuleDeployment(Base):
    """Deployment eines Moduls an einen Kunden."""
    id: UUID
    module_id: UUID
    customer_id: UUID

    # Deployment-Status
    status: "pending" | "deploying" | "deployed" | "failed" | "rolled_back"
    deployed_at: datetime | None
    deployed_by: UUID                  # VendorUser

    # Version
    deployed_version: str
    previous_version: str | None

class ReleaseNote(Base):
    """Release-Notes für Versionen."""
    id: UUID
    module_id: UUID
    version: str

    # Inhalt
    title: str
    changes: list[str]                 # ["Feature X hinzugefügt", "Bug Y behoben"]
    breaking_changes: list[str]

    # Zeitstempel
    published_at: datetime
```

---

## Layer-Dashboard (Hierarchie-Visualisierung)

Das Layer-Dashboard zeigt die gesamte Hierarchie interaktiv an und ermöglicht Navigation und Verwaltung auf allen Ebenen.

### Dashboard-Konzept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FLOWAUDIT - LAYER DASHBOARD                              [vendor_admin]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER-ÜBERSICHT                                        [Vollbild] [Export] │
│  ═══════════════════════════════════════════════════════════════════════════│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 0: FLOWAUDIT GMBH                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Kunden   │ │ Lizenzen │ │ Module   │ │ Releases │ │ Support  │  │   │
│  │  │    12    │ │  847     │ │    8     │ │  v2.4.1  │ │  5 offen │  │   │
│  │  │  aktiv   │ │  genutzt │ │  aktiv   │ │  aktuell │ │  Tickets │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│            ┌─────────────────────────┼─────────────────────────┐           │
│            │                         │                         │           │
│            ▼                         ▼                         ▼           │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐  │
│  │ EU-PRÜFKOORDINATION │ │ BUNDESLÄNDER-       │ │ ÖSTERREICH-         │  │
│  │ (Coordination Body) │ │ VERBUND             │ │ PRÜFVERBUND         │  │
│  │ ───────────────────│ │ ───────────────────│ │ ───────────────────│  │
│  │ 📊 50/50 Lizenzen  │ │ 📊 187/200 Lizenzen│ │ 📊 22/25 Lizenzen  │  │
│  │ 🏢 3 Behörden      │ │ 🏢 14 Behörden     │ │ 🏢 4 Behörden      │  │
│  │ 👥 43 Benutzer     │ │ 👥 187 Benutzer    │ │ 👥 22 Benutzer     │  │
│  │ 📋 12 Templates    │ │ 📋 28 Templates    │ │ 📋 8 Templates     │  │
│  │ ✅ Status: Aktiv   │ │ ⚠️ Status: 94%    │ │ ✅ Status: Aktiv   │  │
│  │                     │ │                     │ │                     │  │
│  │ [Details] [Admin]   │ │ [Details] [Admin]   │ │ [Details] [Admin]   │  │
│  └──────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘  │
│             │                       │                       │             │
│      ┌──────┴──────┐         ┌──────┴──────┐         ┌──────┴──────┐     │
│      │             │         │             │         │             │     │
│      ▼             ▼         ▼             ▼         ▼             ▼     │
│  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐  │
│  │  BRH  │   │LRH BY │   │LRH NRW│   │LRH HE │   │  RH   │   │LRH VBG│  │
│  │ 15 👥 │   │ 12 👥 │   │ 45 👥 │   │ 38 👥 │   │ 10 👥 │   │  6 👥 │  │
│  │  ✅   │   │  ✅   │   │  ✅   │   │  ⚠️   │   │  ✅   │   │  ✅   │  │
│  └───────┘   └───────┘   └───────┘   └───────┘   └───────┘   └───────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Drill-Down: Coordination Body Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EU-PRÜFUNGSKOORDINATION                              ← Zurück zur Übersicht│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KENNZAHLEN                                                                 │
│  ═══════════════════════════════════════════════════════════════════════════│
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  LIZENZEN   │ │  BEHÖRDEN   │ │  BENUTZER   │ │  PRÜFFÄLLE  │           │
│  │  ─────────  │ │  ─────────  │ │  ─────────  │ │  ─────────  │           │
│  │   50 / 50   │ │    3 / 5    │ │     43      │ │    127      │           │
│  │   100% ✅   │ │   60% ⚪    │ │   aktiv     │ │   aktiv     │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                             │
│  PRÜFBEHÖRDEN-HIERARCHIE                                                    │
│  ═══════════════════════════════════════════════════════════════════════════│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🏢 EU-Prüfungskoordination (Coordination Body)                      │   │
│  │    Benutzer: 5 │ Templates: 12 │ Prüffälle auf CB-Ebene: 8         │   │
│  │                                                                     │   │
│  │    ├── 🏛️ Bundesrechnungshof                                       │   │
│  │    │   └─ 👥 15 Benutzer │ 📋 3 eigene Templates │ 📁 45 Prüffälle │   │
│  │    │   └─ 🔵 authority_head: Sabine Meier                          │   │
│  │    │   └─ Teams: Team A (5), Team B (6), Team C (4)                │   │
│  │    │                                                                │   │
│  │    ├── 🏛️ Landesrechnungshof Bayern                                │   │
│  │    │   └─ 👥 12 Benutzer │ 📋 2 eigene Templates │ 📁 38 Prüffälle │   │
│  │    │   └─ 🔵 authority_head: Eva Schwarz                           │   │
│  │    │   └─ Teams: Prüfteam 1 (4), Prüfteam 2 (5)                    │   │
│  │    │                                                                │   │
│  │    └── 🏛️ Landesrechnungshof NRW                                   │   │
│  │        └─ 👥 11 Benutzer │ 📋 1 eigenes Template │ 📁 36 Prüffälle │   │
│  │        └─ 🔵 authority_head: Klaus Weber                           │   │
│  │        └─ Teams: Team Nord (6), Team Süd (5)                       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AKTIONEN                                                                   │
│  ═══════════════════════════════════════════════════════════════════════════│
│  [+ Neue Behörde] [Benutzer verwalten] [Templates] [Stammdaten] [Lizenzen] │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Drill-Down: Prüfbehörde Details

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BUNDESRECHNUNGSHOF                    ← Zurück │ EU-Prüfungskoordination   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAMMDATEN                           KENNZAHLEN                            │
│  ─────────────────────────────────    ─────────────────────────────────     │
│  Name: Bundesrechnungshof             ┌───────────┐ ┌───────────┐          │
│  Kurzname: BRH                        │ BENUTZER  │ │ PRÜFFÄLLE │          │
│  Adresse: Adenauerallee 81            │    15     │ │    45     │          │
│           53113 Bonn                  │   aktiv   │ │   aktiv   │          │
│  Leitung: Präsident Dr. Kay Scheller  └───────────┘ └───────────┘          │
│  E-Mail: poststelle@brh.bund.de                                            │
│                                                                             │
│  BENUTZER NACH ROLLE                                                        │
│  ═══════════════════════════════════════════════════════════════════════════│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔴 authority_head (1)                                               │   │
│  │    └── Sabine Meier (sabine.meier@brh.bund.de)          ✅ aktiv   │   │
│  │                                                                     │   │
│  │ 🟠 team_leader (3)                                                  │   │
│  │    ├── Klaus Fischer (klaus.fischer@brh.bund.de)        ✅ aktiv   │   │
│  │    ├── Maria Schmidt (maria.schmidt@brh.bund.de)        ✅ aktiv   │   │
│  │    └── Thomas Braun (thomas.braun@brh.bund.de)          ✅ aktiv   │   │
│  │                                                                     │   │
│  │ 🟢 auditor (9)                                                      │   │
│  │    ├── Julia Bauer                                      ✅ aktiv   │   │
│  │    ├── Michael Wolf                                     ✅ aktiv   │   │
│  │    ├── ... (7 weitere)                                             │   │
│  │                                                                     │   │
│  │ 🔵 viewer (2)                                                       │   │
│  │    ├── Hans Müller                                      ✅ aktiv   │   │
│  │    └── Lisa Weber                                       ✅ aktiv   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TEAMS                                                                      │
│  ═══════════════════════════════════════════════════════════════════════════│
│  │ Team         │ Leiter         │ Mitglieder │ Aktive Fälle │            │
│  │──────────────│────────────────│────────────│──────────────│            │
│  │ Team A       │ Klaus Fischer  │     5      │      12      │            │
│  │ Team B       │ Maria Schmidt  │     6      │      18      │            │
│  │ Team C       │ Thomas Braun   │     4      │      15      │            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dashboard-Datenmodell

```python
class LayerDashboardData:
    """Aggregierte Daten für das Layer-Dashboard."""

    # Layer 0 Übersicht
    total_customers: int
    total_licenses: int
    used_licenses: int
    active_modules: int
    current_version: str
    open_support_tickets: int

    # Kunden-Liste
    customers: list[CustomerSummary]

class CustomerSummary:
    """Zusammenfassung eines Kunden für das Dashboard."""
    id: UUID
    name: str

    # Lizenzen
    licensed_users: int
    active_users: int
    license_usage_percent: float

    # Struktur
    authority_count: int
    max_authorities: int

    # Status
    status: str
    contract_end: date | None

    # Untergeordnete Behörden
    authorities: list[AuthoritySummary]

class AuthoritySummary:
    """Zusammenfassung einer Prüfbehörde."""
    id: UUID
    name: str
    short_name: str
    user_count: int
    active_cases: int
    authority_head: str
    teams: list[TeamSummary]
```

---

## Gap-Analyse: Aktueller Stand vs. Zielarchitektur

### Implementierungs-Status Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMPLEMENTIERUNGS-STATUS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 0: VENDOR                                              0% ░░░░░░░░░ │
│  ──────────────────────────────────────────────────────────────────────────│
│  ❌ Vendor-Modell                    ❌ Lizenz-Tracking                     │
│  ❌ VendorUser-Modell                ❌ Vendor-Admin-Portal                 │
│  ❌ Customer-Modell                  ❌ Development-Module                  │
│  ❌ vendor_admin Rolle               ❌ Layer-Dashboard                     │
│  ❌ vendor_support Rolle             ❌ Module-Deployment                   │
│                                                                             │
│  LAYER 1: COORDINATION BODY                                  40% ████░░░░░ │
│  ──────────────────────────────────────────────────────────────────────────│
│  ✅ Tenant-Modell (type="group")     ❌ CoordinationBodyProfile             │
│  ✅ group_admin Rolle                ❌ Konzern-Admin-Portal                │
│  ✅ Konzern-Abfragen (GroupQuery)    ❌ Lizenz-Verteilung UI                │
│  ⚠️ Template-System (nur Basis)     ❌ Template-Vererbung                  │
│                                                                             │
│  LAYER 2: PRÜFBEHÖRDE                                        50% █████░░░░ │
│  ──────────────────────────────────────────────────────────────────────────│
│  ✅ Tenant-Modell (type="authority") ❌ AuthorityProfile                    │
│  ✅ authority_head Rolle             ❌ Behörden-Admin-Portal               │
│  ✅ Benutzer-Modell (Basis)          ❌ Benutzer-Verwaltungs-UI             │
│  ✅ Checklisten-Templates            ❌ Template-Überschreibung             │
│  ✅ Dokumenten-Box                   ❌ Team-Verwaltung                     │
│                                                                             │
│  PRÜFFALL-EBENE                                              75% ███████░░ │
│  ──────────────────────────────────────────────────────────────────────────│
│  ✅ AuditCase-Modell                 ✅ Findings                            │
│  ✅ Checklisten                      ✅ Audit-Log                           │
│  ✅ Dokumenten-Box                   ⚠️ Workflow (nur Status)              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Legende: ✅ Implementiert | ⚠️ Teilweise | ❌ Fehlt
```

### Detaillierte Gap-Analyse

| Komponente | Soll (Dokumentation) | Ist (Code) | Gap | Priorität |
|------------|---------------------|------------|-----|-----------|
| **Layer 0** |
| Vendor-Modell | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| VendorUser-Modell | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| Customer-Modell | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| vendor_admin Rolle | Ja | ❌ Nein | Enum erweitern | 🔴 Hoch |
| vendor_support Rolle | Ja | ❌ Nein | Enum erweitern | 🟡 Mittel |
| vendor_developer Rolle | Ja | ❌ Nein | Enum erweitern | 🟡 Mittel |
| LicenseUsage | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| LicenseAlert | Ja | ❌ Nein | Komplett neu | 🟡 Mittel |
| Module-Modell | Ja | ❌ Nein | Komplett neu | 🟡 Mittel |
| ModuleDeployment | Ja | ❌ Nein | Komplett neu | 🟡 Mittel |
| **Layer 1** |
| Tenant (type=group) | Ja | ✅ Ja | - | - |
| CoordinationBodyProfile | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| Template-Hierarchie | Ja | ❌ Nein | Erweitern | 🟡 Mittel |
| **Layer 2** |
| Tenant (type=authority) | Ja | ✅ Ja | - | - |
| AuthorityProfile | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| User (erweitert) | Ja | ⚠️ Teilweise | Felder ergänzen | 🟡 Mittel |
| **Dashboard** |
| Layer-Dashboard | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| Vendor-Portal | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| CB-Admin-Portal | Ja | ❌ Nein | Komplett neu | 🔴 Hoch |
| Authority-Admin | Ja | ❌ Nein | Komplett neu | 🟡 Mittel |

### Erforderliche Änderungen

#### 1. Neue Datenbank-Modelle (Backend)

```
/apps/backend/app/models/
├── vendor.py          # NEU: Vendor, VendorUser
├── customer.py        # NEU: Customer, LicenseUsage, LicenseAlert
├── module.py          # NEU: Module, ModuleDeployment, ReleaseNote
├── profile.py         # NEU: CoordinationBodyProfile, AuthorityProfile
└── user.py            # ERWEITERN: Neue Felder
```

#### 2. Neue API-Endpoints

```
/apps/backend/app/api/
├── vendor.py          # NEU: /api/vendor/*
├── customers.py       # NEU: /api/customers/*
├── licenses.py        # NEU: /api/licenses/*
├── modules.py         # NEU: /api/modules/* (Deployment)
├── profiles.py        # NEU: /api/tenants/*/profile
└── dashboard.py       # NEU: /api/dashboard/layers
```

#### 3. Neue Frontend-Komponenten

```
/apps/frontend/src/
├── views/
│   ├── VendorDashboard.vue       # NEU
│   ├── CustomerManagement.vue    # NEU
│   ├── LicenseOverview.vue       # NEU
│   ├── LayerDashboard.vue        # NEU
│   ├── TenantAdmin.vue           # NEU
│   └── UserManagement.vue        # NEU
├── components/
│   ├── dashboard/
│   │   ├── LayerTree.vue         # NEU
│   │   ├── CustomerCard.vue      # NEU
│   │   ├── LicenseGauge.vue      # NEU
│   │   └── AuthorityNode.vue     # NEU
│   └── admin/
│       ├── ProfileEditor.vue     # NEU
│       └── UserTable.vue         # NEU
```

#### 4. Datenbank-Migrationen

```
/apps/backend/alembic/versions/
├── 007_add_vendor_layer.py         # Vendor, VendorUser
├── 008_add_customer_licensing.py   # Customer, LicenseUsage
├── 009_add_profiles.py             # CoordinationBodyProfile, AuthorityProfile
├── 010_add_modules.py              # Module, ModuleDeployment
├── 011_extend_user.py              # User Erweiterungen
└── 012_add_template_hierarchy.py   # Template parent_id
```

### Geschätzter Aufwand

| Bereich | Aufwand | Abhängigkeiten |
|---------|---------|----------------|
| Layer 0 Backend (Models + API) | 2-3 Wochen | - |
| Layer 0 Frontend (Vendor Portal) | 2-3 Wochen | Backend |
| Layer Dashboard | 1-2 Wochen | Backend |
| Profile-System | 1 Woche | - |
| Lizenz-Tracking | 1 Woche | Customer-Modell |
| Template-Hierarchie | 1-2 Wochen | - |
| Benutzer-Verwaltung UI | 1-2 Wochen | - |
| **Gesamt** | **9-14 Wochen** | |

---

## Umsetzungsplan: Layer-System & Dashboard

### Phase 1: Backend-Grundlagen (2-3 Wochen)

#### 1.1 Datenbank-Modelle erstellen

**Schritt 1: Vendor-Layer Modelle** (`apps/backend/app/models/vendor.py`)
```python
# Neue Datei erstellen mit:
# - Vendor (Softwarefirma)
# - VendorUser (Mitarbeiter)
# - VendorSettings (globale Einstellungen)
```

**Schritt 2: Customer & Lizenz-Modelle** (`apps/backend/app/models/customer.py`)
```python
# Neue Datei erstellen mit:
# - Customer (Kunde mit Lizenzvertrag)
# - LicenseUsage (Tracking)
# - LicenseAlert (Warnungen)
```

**Schritt 3: Profil-Modelle** (`apps/backend/app/models/profile.py`)
```python
# Neue Datei erstellen mit:
# - CoordinationBodyProfile
# - AuthorityProfile
# - Address (embedded)
```

**Schritt 4: User-Modell erweitern** (`apps/backend/app/models/user.py`)
```python
# Bestehende Datei erweitern um:
# - title, phone, mobile, office_location
# - signature_title, signature_department
# - password_changed_at, must_change_password
```

#### 1.2 Alembic-Migrationen

```bash
# Migrationen erstellen und ausführen:
alembic revision --autogenerate -m "add_vendor_layer"
alembic revision --autogenerate -m "add_customer_licensing"
alembic revision --autogenerate -m "add_profiles"
alembic revision --autogenerate -m "extend_user"
alembic upgrade head
```

#### 1.3 Pydantic Schemas

**Neue Schemas** (`apps/backend/app/schemas/`)
```
schemas/
├── vendor.py          # VendorCreate, VendorResponse, VendorUserCreate...
├── customer.py        # CustomerCreate, CustomerResponse, LicenseUsageResponse...
├── profile.py         # CoordinationBodyProfileCreate, AuthorityProfileCreate...
└── dashboard.py       # LayerDashboardData, CustomerSummary, AuthoritySummary...
```

---

### Phase 2: Backend-API (2 Wochen)

#### 2.1 Vendor-API (`apps/backend/app/api/vendor.py`)

```python
# Endpoints:
# GET  /api/vendor                    - Vendor-Info abrufen
# PUT  /api/vendor                    - Vendor-Info aktualisieren
# GET  /api/vendor/users              - Vendor-Mitarbeiter auflisten
# POST /api/vendor/users              - Vendor-Mitarbeiter anlegen
# GET  /api/vendor/settings           - Globale Einstellungen
# PUT  /api/vendor/settings           - Einstellungen aktualisieren
```

#### 2.2 Customers-API (`apps/backend/app/api/customers.py`)

```python
# Endpoints:
# GET    /api/customers               - Alle Kunden auflisten
# POST   /api/customers               - Neuen Kunden anlegen
# GET    /api/customers/{id}          - Kunden-Details
# PUT    /api/customers/{id}          - Kunden aktualisieren
# DELETE /api/customers/{id}          - Kunden deaktivieren
# GET    /api/customers/{id}/licenses - Lizenz-Historie
# PUT    /api/customers/{id}/licenses - Lizenzen anpassen
```

#### 2.3 Layer-Dashboard-API (`apps/backend/app/api/dashboard.py`)

```python
# Endpoints:
# GET /api/dashboard/layers           - Gesamte Layer-Hierarchie
# GET /api/dashboard/layers/{cb_id}   - Coordination Body Details
# GET /api/dashboard/layers/{cb_id}/authorities/{auth_id}  - Behörden-Details
# GET /api/dashboard/stats            - Globale Statistiken
```

**Beispiel-Response für `/api/dashboard/layers`:**
```json
{
  "vendor": {
    "name": "FlowAudit GmbH",
    "stats": {
      "total_customers": 12,
      "total_licenses": 847,
      "used_licenses": 723,
      "active_modules": 8,
      "current_version": "2.4.1",
      "open_support_tickets": 5
    }
  },
  "customers": [
    {
      "id": "uuid...",
      "name": "EU-Prüfungskoordination",
      "licensed_users": 50,
      "active_users": 43,
      "license_usage_percent": 86.0,
      "authority_count": 3,
      "max_authorities": 5,
      "status": "active",
      "authorities": [
        {
          "id": "uuid...",
          "name": "Bundesrechnungshof",
          "short_name": "BRH",
          "user_count": 15,
          "active_cases": 45,
          "authority_head": "Sabine Meier"
        }
      ]
    }
  ]
}
```

#### 2.4 Profile-API (`apps/backend/app/api/profiles.py`)

```python
# Endpoints:
# GET  /api/tenants/{id}/profile      - Profil abrufen
# PUT  /api/tenants/{id}/profile      - Profil aktualisieren
# POST /api/tenants/{id}/profile/logo - Logo hochladen
```

---

### Phase 3: Frontend Layer-Dashboard (2-3 Wochen)

#### 3.1 Vue-Komponenten-Struktur

```
apps/frontend/src/
├── views/
│   ├── LayerDashboard.vue            # Hauptansicht
│   ├── VendorAdmin.vue               # Vendor-Verwaltung
│   ├── CustomerDetail.vue            # Kunden-Detail
│   └── AuthorityDetail.vue           # Behörden-Detail
│
├── components/
│   └── dashboard/
│       ├── LayerTree.vue             # Hierarchie-Baum
│       ├── VendorCard.vue            # Vendor-Übersicht
│       ├── CustomerCard.vue          # Kunden-Kachel
│       ├── AuthorityNode.vue         # Behörden-Knoten
│       ├── LicenseGauge.vue          # Lizenz-Anzeige
│       ├── StatsCard.vue             # Kennzahlen-Karte
│       └── StatusBadge.vue           # Status-Indikator
│
├── composables/
│   ├── useLayerDashboard.ts          # Dashboard-Logik
│   ├── useCustomers.ts               # Kunden-CRUD
│   └── useLicenses.ts                # Lizenz-Tracking
│
└── stores/
    └── layerDashboard.ts             # Pinia Store
```

#### 3.2 LayerDashboard.vue Implementierung

```vue
<template>
  <div class="layer-dashboard">
    <!-- Layer 0: Vendor -->
    <VendorCard
      :vendor="dashboardData.vendor"
      @click="showVendorAdmin"
    />

    <!-- Layer 1: Coordination Bodies -->
    <div class="customers-grid">
      <CustomerCard
        v-for="customer in dashboardData.customers"
        :key="customer.id"
        :customer="customer"
        @click="selectCustomer(customer)"
        @expand="toggleExpand(customer)"
      >
        <!-- Layer 2: Authorities (expandable) -->
        <template v-if="expandedCustomers.includes(customer.id)">
          <AuthorityNode
            v-for="authority in customer.authorities"
            :key="authority.id"
            :authority="authority"
            @click="selectAuthority(authority)"
          />
        </template>
      </CustomerCard>
    </div>

    <!-- Detail-Panel (Sidebar) -->
    <DetailPanel v-if="selectedEntity" :entity="selectedEntity" />
  </div>
</template>
```

#### 3.3 Pinia Store (`stores/layerDashboard.ts`)

```typescript
export const useLayerDashboardStore = defineStore('layerDashboard', () => {
  // State
  const dashboardData = ref<LayerDashboardData | null>(null)
  const selectedCustomerId = ref<string | null>(null)
  const selectedAuthorityId = ref<string | null>(null)
  const expandedCustomers = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const selectedCustomer = computed(() =>
    dashboardData.value?.customers.find(c => c.id === selectedCustomerId.value)
  )

  const selectedAuthority = computed(() =>
    selectedCustomer.value?.authorities.find(a => a.id === selectedAuthorityId.value)
  )

  // Actions
  async function fetchDashboard() {
    loading.value = true
    try {
      const response = await api.get('/dashboard/layers')
      dashboardData.value = response.data
    } catch (e) {
      error.value = 'Dashboard konnte nicht geladen werden'
    } finally {
      loading.value = false
    }
  }

  async function fetchCustomerDetail(customerId: string) {
    const response = await api.get(`/dashboard/layers/${customerId}`)
    // Update customer in dashboardData
  }

  async function fetchAuthorityDetail(customerId: string, authorityId: string) {
    const response = await api.get(`/dashboard/layers/${customerId}/authorities/${authorityId}`)
    // Update authority data
  }

  return {
    dashboardData,
    selectedCustomer,
    selectedAuthority,
    expandedCustomers,
    loading,
    error,
    fetchDashboard,
    fetchCustomerDetail,
    fetchAuthorityDetail,
  }
})
```

#### 3.4 Router-Konfiguration

```typescript
// router/index.ts - Neue Routes hinzufügen
{
  path: '/admin',
  component: AdminLayout,
  meta: { requiresAuth: true, roles: ['vendor_admin', 'vendor_support'] },
  children: [
    {
      path: 'dashboard',
      name: 'layer-dashboard',
      component: () => import('@/views/LayerDashboard.vue'),
    },
    {
      path: 'customers',
      name: 'customer-management',
      component: () => import('@/views/CustomerManagement.vue'),
    },
    {
      path: 'customers/:id',
      name: 'customer-detail',
      component: () => import('@/views/CustomerDetail.vue'),
    },
    {
      path: 'customers/:customerId/authorities/:authorityId',
      name: 'authority-detail',
      component: () => import('@/views/AuthorityDetail.vue'),
    },
  ],
}
```

---

### Phase 4: Admin-Portale (2-3 Wochen)

#### 4.1 Vendor-Admin-Portal

```
VendorAdmin.vue
├── Tabs:
│   ├── Kunden-Übersicht (CustomerList.vue)
│   ├── Lizenz-Management (LicenseManager.vue)
│   ├── Globale Templates (TemplateManager.vue)
│   ├── System-Einstellungen (VendorSettings.vue)
│   └── Support-Tickets (SupportTickets.vue)
```

#### 4.2 Coordination Body Admin

```
TenantAdmin.vue (für group_admin)
├── Tabs:
│   ├── Prüfbehörden (AuthorityList.vue)
│   ├── Benutzer (UserManager.vue)
│   ├── Templates (TenantTemplates.vue)
│   ├── Stammdaten (ProfileEditor.vue)
│   └── Lizenzen (LicenseAllocation.vue)
```

#### 4.3 Authority Admin

```
AuthorityAdmin.vue (für authority_head)
├── Tabs:
│   ├── Benutzer (UserManager.vue)
│   ├── Teams (TeamManager.vue)
│   ├── Templates (AuthorityTemplates.vue)
│   └── Stammdaten (ProfileEditor.vue)
```

---

### Phase 5: Integration & Testing (1-2 Wochen)

#### 5.1 Berechtigungsprüfung

```python
# apps/backend/app/core/permissions.py
class LayerPermissions:
    @staticmethod
    def can_access_vendor(user: User) -> bool:
        return user.role in ['vendor_admin', 'vendor_support']

    @staticmethod
    def can_manage_customer(user: User, customer_id: UUID) -> bool:
        if user.role == 'vendor_admin':
            return True
        if user.role == 'group_admin':
            return user.tenant.customer_id == customer_id
        return False

    @staticmethod
    def can_manage_authority(user: User, authority_id: UUID) -> bool:
        if user.role in ['vendor_admin', 'group_admin']:
            return True
        if user.role == 'authority_head':
            return user.tenant_id == authority_id
        return False
```

#### 5.2 Tests

```python
# tests/api/test_dashboard.py
class TestLayerDashboard:
    async def test_vendor_admin_sees_all_customers(self):
        # ...

    async def test_group_admin_sees_only_own_customer(self):
        # ...

    async def test_authority_head_sees_only_own_authority(self):
        # ...

# tests/api/test_customers.py
class TestCustomerAPI:
    async def test_create_customer(self):
        # ...

    async def test_license_tracking(self):
        # ...
```

#### 5.3 E2E Tests

```typescript
// tests/e2e/layer-dashboard.spec.ts
describe('Layer Dashboard', () => {
  it('vendor_admin can see all layers', () => {
    // Login as vendor_admin
    // Navigate to /admin/dashboard
    // Assert all customers visible
    // Click on customer -> authorities visible
    // Click on authority -> details visible
  })

  it('group_admin can only see own customer', () => {
    // ...
  })
})
```

---

### Phase 6: Deployment & Rollout (1 Woche)

#### 6.1 Migrations-Strategie

```bash
# 1. Backup erstellen
pg_dump flowaudit > backup_before_layer.sql

# 2. Migrationen in Staging testen
alembic upgrade head

# 3. Seed-Daten für Vendor
python scripts/seed_vendor.py

# 4. Bestehende Tenants als Customers migrieren
python scripts/migrate_tenants_to_customers.py

# 5. Production-Deployment
docker-compose up -d --build
```

#### 6.2 Feature-Flags

```python
# apps/backend/app/core/feature_flags.py
FEATURE_FLAGS = {
    "layer_dashboard": True,      # Layer-Dashboard aktivieren
    "vendor_portal": True,        # Vendor-Portal aktivieren
    "license_tracking": True,     # Lizenz-Tracking aktivieren
    "template_hierarchy": False,  # Template-Hierarchie (Phase 2)
}
```

---

### Implementierungs-Reihenfolge (Zusammenfassung)

```
Woche 1-2:  ┌─────────────────────────────────────────┐
            │ Phase 1: Backend-Modelle & Migrationen  │
            │ - Vendor, Customer, Profile Modelle     │
            │ - Alembic Migrationen                   │
            │ - Pydantic Schemas                      │
            └─────────────────────────────────────────┘
                              │
                              ▼
Woche 3-4:  ┌─────────────────────────────────────────┐
            │ Phase 2: Backend-API                    │
            │ - Vendor-API                            │
            │ - Customers-API                         │
            │ - Dashboard-API                         │
            │ - Profile-API                           │
            └─────────────────────────────────────────┘
                              │
                              ▼
Woche 5-7:  ┌─────────────────────────────────────────┐
            │ Phase 3: Frontend Layer-Dashboard       │
            │ - Vue-Komponenten                       │
            │ - Pinia Store                           │
            │ - Router-Integration                    │
            └─────────────────────────────────────────┘
                              │
                              ▼
Woche 8-10: ┌─────────────────────────────────────────┐
            │ Phase 4: Admin-Portale                  │
            │ - Vendor-Admin-Portal                   │
            │ - CB-Admin-Portal                       │
            │ - Authority-Admin-Portal                │
            └─────────────────────────────────────────┘
                              │
                              ▼
Woche 11-12:┌─────────────────────────────────────────┐
            │ Phase 5 & 6: Testing & Deployment       │
            │ - Unit Tests                            │
            │ - E2E Tests                             │
            │ - Staging-Deployment                    │
            │ - Production-Rollout                    │
            └─────────────────────────────────────────┘
```

---

### Abhängigkeiten zwischen Komponenten

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ABHÄNGIGKEITS-GRAPH                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Vendor-Modell ─────┬────────────────────────────────────────────────┐  │
│        │            │                                                │  │
│        ▼            ▼                                                │  │
│  VendorUser    Customer-Modell ───────┬──────────────────────────┐  │  │
│        │            │                  │                          │  │  │
│        │            ▼                  ▼                          ▼  │  │
│        │     LicenseUsage      LicenseAlert              Profile  │  │  │
│        │            │                  │                     │    │  │  │
│        └────────────┼──────────────────┼─────────────────────┼────┘  │  │
│                     │                  │                     │       │  │
│                     └──────────────────┴─────────────────────┘       │  │
│                                    │                                 │  │
│                                    ▼                                 │  │
│                            Dashboard-API ◄───────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│                          LayerDashboard.vue                             │
│                           │          │                                  │
│              ┌────────────┘          └────────────┐                     │
│              ▼                                    ▼                     │
│       CustomerCard.vue                    AuthorityNode.vue             │
│              │                                    │                     │
│              ▼                                    ▼                     │
│    CustomerDetail.vue                   AuthorityDetail.vue             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
