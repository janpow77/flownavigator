# Implementiere Module Converter Models

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Dateien um den Kontext zu verstehen
2. Implementiere alle beschriebenen Komponenten vollständig
3. Behebe Fehler eigenständig (Imports, Typen, Abhängigkeiten)
4. Führe die Validierung am Ende durch
5. Wenn Tests fehlschlagen: Analysiere und behebe die Fehler
6. Committe und pushe erst wenn alles funktioniert
7. Fahre dann mit `/implement-llm-service` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle die SQLAlchemy Models für den Module Converter basierend auf der Planung in `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`.

## Zu erstellende Models

### 1. Konzern Model (`backend/app/models/konzern.py`)
```python
class Konzern(Base):
    __tablename__ = "konzerne"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # URL-freundlich
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    organizations: Mapped[List["Organization"]] = relationship(back_populates="konzern")
    llm_configurations: Mapped[List["LLMConfiguration"]] = relationship(back_populates="konzern")
```

### 2. Organization erweitern (`backend/app/models/organization.py`)
- Füge `konzern_id` Foreign Key hinzu
- Füge Relationship zu Konzern hinzu

### 3. LLMConfiguration Model (`backend/app/models/llm_configuration.py`)
```python
class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"
    GLM = "glm"

class LLMConfiguration(Base):
    __tablename__ = "llm_configurations"

    id: Mapped[int] = mapped_column(primary_key=True)
    layer: Mapped[str] = mapped_column(String(20))  # rahmen, konzern, orga
    konzern_id: Mapped[Optional[int]] = mapped_column(ForeignKey("konzerne.id"), nullable=True)
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), nullable=True)

    provider: Mapped[LLMProvider] = mapped_column(SQLAlchemyEnum(LLMProvider))
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100))

    monthly_budget_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    current_month_usage_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    priority: Mapped[int] = mapped_column(default=1)  # 1=primär, 2=fallback, etc.
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('layer', 'konzern_id', 'organization_id', 'provider', name='uq_llm_config_layer'),
        Index('ix_llm_config_lookup', 'layer', 'konzern_id', 'organization_id', 'is_active'),
    )
```

### 4. ModuleTemplate Model (`backend/app/models/module_template.py`)
```python
class ModuleStatus(str, Enum):
    DRAFT = "draft"
    DEV = "dev"
    TEST = "test"
    FREIGABE = "freigabe"
    PROD = "prod"
    ARCHIVED = "archived"

class ModuleTemplate(Base):
    __tablename__ = "module_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Versioning
    version_major: Mapped[int] = mapped_column(default=1)
    version_minor: Mapped[int] = mapped_column(default=0)
    version_patch: Mapped[int] = mapped_column(default=0)

    # Content
    tree_structure: Mapped[dict] = mapped_column(JSONB)  # Das generierte Prüfschema
    source_catalog: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Original-Katalog

    # Metadata
    layer: Mapped[str] = mapped_column(String(20))  # rahmen, konzern, orga
    konzern_id: Mapped[Optional[int]] = mapped_column(ForeignKey("konzerne.id"), nullable=True)
    organization_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizations.id"), nullable=True)

    status: Mapped[ModuleStatus] = mapped_column(SQLAlchemyEnum(ModuleStatus), default=ModuleStatus.DRAFT)

    # Audit
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # GitHub Integration
    github_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_pr_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Parent for versioning
    parent_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("module_templates.id"), nullable=True)

    __table_args__ = (
        Index('ix_module_template_lookup', 'layer', 'konzern_id', 'status'),
    )
```

### 5. ModuleConversionLog Model (`backend/app/models/module_conversion_log.py`)
```python
class ConversionStep(str, Enum):
    UPLOAD = "upload"
    PARSING = "parsing"
    LLM_CONVERSION = "llm_conversion"
    VALIDATION = "validation"
    REVIEW = "review"
    STAGING = "staging"

class ModuleConversionLog(Base):
    __tablename__ = "module_conversion_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_template_id: Mapped[int] = mapped_column(ForeignKey("module_templates.id"))

    step: Mapped[ConversionStep] = mapped_column(SQLAlchemyEnum(ConversionStep))
    status: Mapped[str] = mapped_column(String(20))  # started, completed, failed

    llm_provider_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_tokens_input: Mapped[Optional[int]] = mapped_column(nullable=True)
    llm_tokens_output: Mapped[Optional[int]] = mapped_column(nullable=True)
    llm_cost_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

## Schritte

1. Erstelle die Model-Dateien in `backend/app/models/`
2. Aktualisiere `backend/app/models/__init__.py` mit den neuen Imports
3. Erstelle Alembic Migration: `alembic revision --autogenerate -m "Add module converter models"`
4. Teste die Migration: `alembic upgrade head`
5. Erstelle entsprechende Pydantic Schemas in `backend/app/schemas/`

## Referenzen
- Bestehende Models: `backend/app/models/`
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`
- Layer-Architektur: `docs/LAYER_ARCHITECTURE.md`

## Validierung
Nach Abschluss:
```bash
cd backend
alembic upgrade head
pytest tests/ -v
```
