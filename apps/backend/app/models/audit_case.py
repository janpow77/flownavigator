"""Audit Case models - Prüfungsfälle."""

from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class AuditCase(Base, TimestampMixin):
    """Prüfungsfall - Einzelne Vorhabenprüfung."""

    __tablename__ = "audit_cases"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fiscal_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Vorhaben-Referenz
    case_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    project_name: Mapped[str] = mapped_column(String(500), nullable=False)
    beneficiary_name: Mapped[str] = mapped_column(String(500), nullable=False)

    # Finanzielle Daten
    approved_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    audited_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    irregular_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",  # Entwurf
            "in_progress",  # In Bearbeitung
            "review",  # Prüfung durch Teamleiter
            "completed",  # Abgeschlossen
            "archived",  # Archiviert
            name="audit_case_status",
        ),
        default="draft",
        nullable=False,
        index=True,
    )

    # Prüfungsart
    audit_type: Mapped[str] = mapped_column(
        Enum(
            "operation",  # Vorhabenprüfung
            "system",  # Systemprüfung
            "accounts",  # Rechnungslegungsprüfung
            name="audit_type",
        ),
        default="operation",
        nullable=False,
    )

    # Prüfungszeitraum
    audit_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    audit_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Prüfteam
    primary_auditor_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    secondary_auditor_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_leader_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Prüfungsergebnis
    result: Mapped[str | None] = mapped_column(
        Enum(
            "no_findings",  # Keine Feststellungen
            "findings_minor",  # Geringfügige Feststellungen
            "findings_major",  # Wesentliche Feststellungen
            "irregularity",  # Unregelmäßigkeit
            name="audit_result",
        ),
        nullable=True,
    )

    # Dynamische Felder (Stammdaten, Belegliste etc.)
    custom_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Flags
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notizen
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_cases")  # type: ignore
    primary_auditor: Mapped["User | None"] = relationship(  # type: ignore
        "User",
        foreign_keys=[primary_auditor_id],
        back_populates="primary_audits",
    )
    secondary_auditor: Mapped["User | None"] = relationship(  # type: ignore
        "User",
        foreign_keys=[secondary_auditor_id],
        back_populates="secondary_audits",
    )
    team_leader: Mapped["User | None"] = relationship(  # type: ignore
        "User",
        foreign_keys=[team_leader_id],
        back_populates="led_audits",
    )
    checklists: Mapped[list["AuditCaseChecklist"]] = relationship(
        "AuditCaseChecklist",
        back_populates="audit_case",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["AuditCaseFinding"]] = relationship(
        "AuditCaseFinding",
        back_populates="audit_case",
        cascade="all, delete-orphan",
    )
    document_box: Mapped["DocumentBox | None"] = relationship(  # type: ignore
        "DocumentBox",
        back_populates="audit_case",
        uselist=False,
    )


class AuditCaseChecklist(Base, TimestampMixin):
    """Checkliste zu einem Prüfungsfall."""

    __tablename__ = "audit_case_checklists"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    audit_case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("audit_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checklist_template_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("checklist_templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Typ
    checklist_type: Mapped[str] = mapped_column(
        Enum(
            "main",  # Hauptcheckliste
            "procurement",  # Vergabeprüfung
            "subsidy",  # Beihilfeprüfung
            "eligibility",  # Förderfähigkeit
            "custom",  # Benutzerdefiniert
            name="checklist_type",
        ),
        default="main",
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        Enum("not_started", "in_progress", "completed", name="checklist_status"),
        default="not_started",
        nullable=False,
    )

    # Fortschritt
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0)

    # Antworten (JSONB)
    responses: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Bearbeiter
    completed_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship
    audit_case: Mapped["AuditCase"] = relationship(
        "AuditCase",
        back_populates="checklists",
    )


class AuditCaseFinding(Base, TimestampMixin):
    """Feststellung zu einem Prüfungsfall."""

    __tablename__ = "audit_case_findings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    audit_case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("audit_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Feststellungsnummer
    finding_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Typ
    finding_type: Mapped[str] = mapped_column(
        Enum(
            "irregularity",  # Unregelmäßigkeit
            "deficiency",  # Mangel
            "recommendation",  # Empfehlung
            "observation",  # Beobachtung
            name="finding_type",
        ),
        nullable=False,
    )

    # Fehlerart (EU-Kategorien)
    error_category: Mapped[str | None] = mapped_column(
        Enum(
            "ineligible_expenditure",  # Nicht förderfähige Ausgaben
            "public_procurement",  # Vergabefehler
            "missing_documents",  # Fehlende Unterlagen
            "calculation_error",  # Rechenfehler
            "double_funding",  # Doppelfinanzierung
            "other",  # Sonstiges
            name="error_category",
        ),
        nullable=True,
    )

    # Beschreibung
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Finanzieller Impact
    financial_impact: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    is_systemic: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status der Feststellung
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "confirmed",
            "disputed",  # Widerspruch
            "resolved",  # Behoben
            "withdrawn",  # Zurückgezogen
            name="finding_status",
        ),
        default="draft",
        nullable=False,
    )

    # Stellungnahme
    response_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    response_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    response_received: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Abschluss
    final_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    audit_case: Mapped["AuditCase"] = relationship(
        "AuditCase",
        back_populates="findings",
    )


class FiscalYear(Base, TimestampMixin):
    """Prüfjahr / Haushaltsjahr."""

    __tablename__ = "fiscal_years"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum(
            "planning",  # Planung
            "active",  # Aktiv
            "closing",  # Abschluss
            "closed",  # Abgeschlossen
            name="fiscal_year_status",
        ),
        default="planning",
        nullable=False,
    )

    # Konfiguration
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Statistics (cached)
    statistics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class ChecklistTemplate(Base, TimestampMixin):
    """Checklisten-Vorlage."""

    __tablename__ = "checklist_templates"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Version
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # Typ
    checklist_type: Mapped[str] = mapped_column(
        Enum(
            "main",
            "procurement",
            "subsidy",
            "eligibility",
            "system",
            "custom",
            name="template_checklist_type",
        ),
        default="main",
        nullable=False,
    )

    # Struktur (JSONB)
    structure: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        Enum("draft", "published", "archived", name="template_status"),
        default="draft",
        nullable=False,
    )
