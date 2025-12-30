"""Checklist schemas."""

from datetime import datetime
from typing import Optional, Any, Literal

from pydantic import BaseModel, Field, ConfigDict


# --- Question Types ---

QuestionType = Literal[
    "text",  # Freitext
    "textarea",  # Mehrzeiliger Text
    "number",  # Zahl
    "currency",  # Währungsbetrag
    "date",  # Datum
    "yes_no",  # Ja/Nein
    "yes_no_na",  # Ja/Nein/N.A.
    "select",  # Auswahl (Single)
    "multiselect",  # Mehrfachauswahl
    "rating",  # Bewertung (1-5)
    "file",  # Dateianhang
    "section",  # Abschnittsüberschrift (keine Eingabe)
]


# --- Question Schema ---


class QuestionOption(BaseModel):
    """Option für Select/Multiselect Fragen."""

    value: str
    label: str
    description: Optional[str] = None


class QuestionSchema(BaseModel):
    """Schema für eine einzelne Frage."""

    id: str = Field(..., description="Eindeutige ID der Frage")
    type: QuestionType
    label: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    placeholder: Optional[str] = None

    # Validierung
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex für Validierung

    # Optionen für Select/Multiselect
    options: Optional[list[QuestionOption]] = None

    # Bedingte Anzeige
    condition: Optional[dict[str, Any]] = (
        None  # z.B. {"question_id": "q1", "value": "yes"}
    )

    # Gruppierung
    group: Optional[str] = None
    order: int = 0

    # Für Berichtsübernahme
    report_include: bool = True
    report_label: Optional[str] = None


class SectionSchema(BaseModel):
    """Schema für einen Abschnitt."""

    id: str
    title: str
    description: Optional[str] = None
    questions: list[QuestionSchema] = Field(default_factory=list)
    order: int = 0


# --- Template Schemas ---


class ChecklistTemplateBase(BaseModel):
    """Base schema for checklist template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    checklist_type: str = "main"


class ChecklistTemplateCreate(ChecklistTemplateBase):
    """Schema for creating a checklist template."""

    structure: dict[str, Any] = Field(
        default_factory=lambda: {"sections": [], "settings": {}},
        description="Template structure with sections and questions",
    )


class ChecklistTemplateUpdate(BaseModel):
    """Schema for updating a checklist template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    checklist_type: Optional[str] = None
    structure: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class ChecklistTemplateResponse(ChecklistTemplateBase):
    """Schema for checklist template response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    version: int
    is_current: bool
    structure: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class ChecklistTemplateListResponse(BaseModel):
    """Paginated list of templates."""

    items: list[ChecklistTemplateResponse]
    total: int


class ChecklistTemplateSummary(BaseModel):
    """Summary schema for template selection."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    checklist_type: str
    version: int
    questions_count: int = 0


# --- Checklist Instance Schemas ---


class QuestionResponse(BaseModel):
    """Response to a single question."""

    question_id: str
    value: Any
    note: Optional[str] = None
    attachments: list[str] = Field(default_factory=list)
    answered_at: Optional[datetime] = None
    answered_by: Optional[str] = None


class ChecklistCreateFromTemplate(BaseModel):
    """Schema for creating a checklist from a template."""

    template_id: str
    checklist_type: Optional[str] = None


class ChecklistResponseUpdate(BaseModel):
    """Schema for updating checklist responses."""

    responses: dict[str, Any]  # question_id -> response value
    status: Optional[str] = None
    notes: Optional[dict[str, str]] = None  # question_id -> note


class ChecklistInstanceResponse(BaseModel):
    """Full checklist instance response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_case_id: str
    checklist_template_id: Optional[str]
    checklist_type: str
    status: str
    progress: int
    total_questions: int
    answered_questions: int
    responses: dict[str, Any]
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Include template structure for rendering
    template_name: Optional[str] = None
    structure: Optional[dict[str, Any]] = None


class ChecklistSummaryResponse(BaseModel):
    """Summary for list view."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    checklist_type: str
    template_name: Optional[str] = None
    status: str
    progress: int
    total_questions: int
    answered_questions: int
    created_at: datetime
    updated_at: datetime


# --- Default Template Structures ---


def get_default_main_checklist() -> dict[str, Any]:
    """Get default structure for main checklist (Hauptcheckliste)."""
    return {
        "settings": {
            "allow_partial_save": True,
            "require_all_questions": False,
            "show_progress": True,
        },
        "sections": [
            {
                "id": "general",
                "title": "Allgemeine Angaben",
                "order": 1,
                "questions": [
                    {
                        "id": "q1",
                        "type": "text",
                        "label": "Aktenzeichen des Vorhabens",
                        "required": True,
                        "order": 1,
                    },
                    {
                        "id": "q2",
                        "type": "date",
                        "label": "Datum der Vor-Ort-Prüfung",
                        "required": True,
                        "order": 2,
                    },
                    {
                        "id": "q3",
                        "type": "textarea",
                        "label": "Teilnehmer der Prüfung",
                        "placeholder": "Name, Funktion",
                        "order": 3,
                    },
                ],
            },
            {
                "id": "eligibility",
                "title": "Förderfähigkeit",
                "order": 2,
                "questions": [
                    {
                        "id": "q4",
                        "type": "yes_no_na",
                        "label": "Ist der Begünstigte förderfähig?",
                        "required": True,
                        "order": 1,
                    },
                    {
                        "id": "q5",
                        "type": "yes_no_na",
                        "label": "Entspricht das Vorhaben den Fördervoraussetzungen?",
                        "required": True,
                        "order": 2,
                    },
                    {
                        "id": "q6",
                        "type": "textarea",
                        "label": "Bemerkungen zur Förderfähigkeit",
                        "order": 3,
                    },
                ],
            },
            {
                "id": "expenditure",
                "title": "Ausgabenprüfung",
                "order": 3,
                "questions": [
                    {
                        "id": "q7",
                        "type": "yes_no_na",
                        "label": "Sind die geltend gemachten Ausgaben förderfähig?",
                        "required": True,
                        "order": 1,
                    },
                    {
                        "id": "q8",
                        "type": "yes_no_na",
                        "label": "Wurden die Originalbelege vorgelegt?",
                        "required": True,
                        "order": 2,
                    },
                    {
                        "id": "q9",
                        "type": "currency",
                        "label": "Summe der geprüften Ausgaben",
                        "order": 3,
                    },
                    {
                        "id": "q10",
                        "type": "currency",
                        "label": "Summe der nicht förderfähigen Ausgaben",
                        "order": 4,
                    },
                ],
            },
            {
                "id": "documentation",
                "title": "Dokumentation",
                "order": 4,
                "questions": [
                    {
                        "id": "q11",
                        "type": "yes_no",
                        "label": "Ist die Projektdokumentation vollständig?",
                        "order": 1,
                    },
                    {
                        "id": "q12",
                        "type": "yes_no",
                        "label": "Wurden die Publizitätsvorschriften eingehalten?",
                        "order": 2,
                    },
                ],
            },
            {
                "id": "result",
                "title": "Prüfungsergebnis",
                "order": 5,
                "questions": [
                    {
                        "id": "q13",
                        "type": "select",
                        "label": "Gesamtergebnis der Prüfung",
                        "required": True,
                        "options": [
                            {"value": "no_findings", "label": "Keine Feststellungen"},
                            {
                                "value": "findings_minor",
                                "label": "Geringfügige Feststellungen",
                            },
                            {
                                "value": "findings_major",
                                "label": "Wesentliche Feststellungen",
                            },
                            {"value": "irregularity", "label": "Unregelmäßigkeit"},
                        ],
                        "order": 1,
                    },
                    {
                        "id": "q14",
                        "type": "textarea",
                        "label": "Zusammenfassung der Prüfungsergebnisse",
                        "required": True,
                        "order": 2,
                    },
                ],
            },
        ],
    }


def get_default_procurement_checklist() -> dict[str, Any]:
    """Get default structure for procurement checklist (Vergabeprüfung)."""
    return {
        "settings": {
            "allow_partial_save": True,
            "require_all_questions": False,
        },
        "sections": [
            {
                "id": "threshold",
                "title": "Schwellenwertprüfung",
                "order": 1,
                "questions": [
                    {
                        "id": "p1",
                        "type": "currency",
                        "label": "Auftragswert (netto)",
                        "required": True,
                        "order": 1,
                    },
                    {
                        "id": "p2",
                        "type": "select",
                        "label": "Anwendbares Vergaberecht",
                        "required": True,
                        "options": [
                            {"value": "vob", "label": "VOB/A"},
                            {"value": "vgv", "label": "VgV"},
                            {"value": "uvgo", "label": "UVgO"},
                            {"value": "other", "label": "Sonstiges"},
                        ],
                        "order": 2,
                    },
                ],
            },
            {
                "id": "procedure",
                "title": "Vergabeverfahren",
                "order": 2,
                "questions": [
                    {
                        "id": "p3",
                        "type": "select",
                        "label": "Art des Vergabeverfahrens",
                        "required": True,
                        "options": [
                            {"value": "direct", "label": "Direktvergabe"},
                            {"value": "limited", "label": "Beschränkte Ausschreibung"},
                            {"value": "public", "label": "Öffentliche Ausschreibung"},
                            {"value": "negotiated", "label": "Verhandlungsverfahren"},
                        ],
                        "order": 1,
                    },
                    {
                        "id": "p4",
                        "type": "yes_no_na",
                        "label": "Wurde das korrekte Verfahren angewendet?",
                        "required": True,
                        "order": 2,
                    },
                    {
                        "id": "p5",
                        "type": "yes_no_na",
                        "label": "Wurde der Auftrag ordnungsgemäß veröffentlicht?",
                        "order": 3,
                    },
                ],
            },
            {
                "id": "award",
                "title": "Zuschlagsentscheidung",
                "order": 3,
                "questions": [
                    {
                        "id": "p6",
                        "type": "number",
                        "label": "Anzahl der eingegangenen Angebote",
                        "order": 1,
                    },
                    {
                        "id": "p7",
                        "type": "yes_no_na",
                        "label": "Wurden die Zuschlagskriterien vorab festgelegt?",
                        "required": True,
                        "order": 2,
                    },
                    {
                        "id": "p8",
                        "type": "yes_no_na",
                        "label": "Wurde die Vergabeentscheidung dokumentiert?",
                        "required": True,
                        "order": 3,
                    },
                ],
            },
            {
                "id": "result",
                "title": "Ergebnis",
                "order": 4,
                "questions": [
                    {
                        "id": "p9",
                        "type": "select",
                        "label": "Bewertung der Vergabe",
                        "required": True,
                        "options": [
                            {"value": "compliant", "label": "Vergabekonform"},
                            {"value": "minor_defects", "label": "Geringfügige Mängel"},
                            {"value": "major_defects", "label": "Wesentliche Mängel"},
                            {"value": "violation", "label": "Vergaberechtsverstoß"},
                        ],
                        "order": 1,
                    },
                    {
                        "id": "p10",
                        "type": "textarea",
                        "label": "Bemerkungen",
                        "order": 2,
                    },
                ],
            },
        ],
    }
