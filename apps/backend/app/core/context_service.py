"""Context Service for LLM Context Building (AC-7.1.4).

This service builds context for LLM conversations based on the context type.
"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.history import LLMMessage
from app.models.audit_case import AuditCase, AuditCaseChecklist, AuditCaseFinding
from app.schemas.history import ContextResponse, LLMMessageResponse


class ContextService:
    """Service for building LLM context.

    AC-7.1.4: Kontext wird korrekt aufgebaut
    """

    # Context type to system prompt mapping
    SYSTEM_PROMPTS = {
        "audit_case": """Du bist ein Assistent für die Prüfung von EU-Förderprojekten.
Du hilfst bei der Analyse von Projekten, der Erstellung von Prüfberichten und der Identifikation von Feststellungen.
Antworte präzise und fachlich korrekt auf Deutsch.""",
        "checklist": """Du bist ein Assistent für die Bearbeitung von Prüfungschecklisten.
Du hilfst bei der Beantwortung von Prüfungsfragen und der Dokumentation von Ergebnissen.
Antworte präzise und orientiere dich an den geltenden Verwaltungsvorschriften.""",
        "finding": """Du bist ein Assistent für die Analyse und Formulierung von Feststellungen.
Du hilfst bei der rechtlichen Einordnung und der Berechnung von Korrekturbeträgen.
Antworte fachlich fundiert und berücksichtige die relevanten EU-Verordnungen.""",
        "document": """Du bist ein Assistent für die Dokumentenanalyse.
Du hilfst bei der Extraktion von Informationen aus Projektdokumenten.
Analysiere den Inhalt sorgfältig und fasse die wichtigsten Punkte zusammen.""",
        "general": """Du bist ein hilfreicher Assistent für die Prüfungsbehörde.
Du beantwortest Fragen zur EU-Förderung und unterstützt bei Verwaltungsaufgaben.
Antworte klar und verständlich auf Deutsch.""",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_context(
        self,
        tenant_id: str,
        context_type: str,
        context_id: Optional[str] = None,
        include_history: bool = True,
        max_messages: int = 10,
        conversation_id: Optional[str] = None,
    ) -> ContextResponse:
        """Build context for LLM based on context type.

        Args:
            tenant_id: Current tenant ID
            context_type: Type of context (audit_case, checklist, finding, etc.)
            context_id: Optional ID of the context entity
            include_history: Whether to include conversation history
            max_messages: Maximum number of recent messages to include
            conversation_id: Optional conversation ID to get history from

        Returns:
            ContextResponse with system prompt, context data, and recent messages
        """
        # Get system prompt
        system_prompt = self.SYSTEM_PROMPTS.get(
            context_type, self.SYSTEM_PROMPTS["general"]
        )

        # Build context data based on type
        context_data = await self._get_context_data(tenant_id, context_type, context_id)

        # Get recent messages if requested
        recent_messages: list[LLMMessageResponse] = []
        total_tokens = 0

        if include_history and conversation_id:
            messages, tokens = await self._get_recent_messages(
                conversation_id, max_messages
            )
            recent_messages = messages
            total_tokens = tokens

        # Enhance system prompt with context data
        enhanced_prompt = self._enhance_prompt(system_prompt, context_data)

        return ContextResponse(
            system_prompt=enhanced_prompt,
            context_data=context_data,
            recent_messages=recent_messages,
            total_context_tokens=total_tokens + self._estimate_tokens(enhanced_prompt),
        )

    async def _get_context_data(
        self,
        tenant_id: str,
        context_type: str,
        context_id: Optional[str],
    ) -> dict[str, Any]:
        """Get context data based on type and ID."""
        if not context_id:
            return {"type": context_type}

        if context_type == "audit_case":
            return await self._get_audit_case_context(tenant_id, context_id)
        elif context_type == "checklist":
            return await self._get_checklist_context(tenant_id, context_id)
        elif context_type == "finding":
            return await self._get_finding_context(tenant_id, context_id)
        else:
            return {"type": context_type, "id": context_id}

    async def _get_audit_case_context(
        self, tenant_id: str, case_id: str
    ) -> dict[str, Any]:
        """Get audit case context data."""
        result = await self.db.execute(
            select(AuditCase).where(
                AuditCase.id == case_id,
                AuditCase.tenant_id == tenant_id,
            )
        )
        case = result.scalar_one_or_none()

        if not case:
            return {"type": "audit_case", "id": case_id, "error": "not_found"}

        return {
            "type": "audit_case",
            "id": case.id,
            "project_name": case.project_name,
            "project_number": case.project_number,
            "beneficiary": case.beneficiary,
            "program": case.program,
            "status": case.status,
            "funding_amount": str(case.funding_amount) if case.funding_amount else None,
            "audit_type": case.audit_type,
        }

    async def _get_checklist_context(
        self, tenant_id: str, checklist_id: str
    ) -> dict[str, Any]:
        """Get checklist context data."""
        result = await self.db.execute(
            select(AuditCaseChecklist).where(
                AuditCaseChecklist.id == checklist_id,
            )
        )
        checklist = result.scalar_one_or_none()

        if not checklist:
            return {"type": "checklist", "id": checklist_id, "error": "not_found"}

        # Get parent case
        case_result = await self.db.execute(
            select(AuditCase).where(
                AuditCase.id == checklist.audit_case_id,
                AuditCase.tenant_id == tenant_id,
            )
        )
        case = case_result.scalar_one_or_none()

        return {
            "type": "checklist",
            "id": checklist.id,
            "name": checklist.name,
            "audit_case_id": checklist.audit_case_id,
            "project_name": case.project_name if case else None,
        }

    async def _get_finding_context(
        self, tenant_id: str, finding_id: str
    ) -> dict[str, Any]:
        """Get finding context data."""
        result = await self.db.execute(
            select(AuditCaseFinding).where(
                AuditCaseFinding.id == finding_id,
            )
        )
        finding = result.scalar_one_or_none()

        if not finding:
            return {"type": "finding", "id": finding_id, "error": "not_found"}

        # Get parent case
        case_result = await self.db.execute(
            select(AuditCase).where(
                AuditCase.id == finding.audit_case_id,
                AuditCase.tenant_id == tenant_id,
            )
        )
        case = case_result.scalar_one_or_none()

        return {
            "type": "finding",
            "id": finding.id,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "status": finding.status,
            "audit_case_id": finding.audit_case_id,
            "project_name": case.project_name if case else None,
        }

    async def _get_recent_messages(
        self, conversation_id: str, max_messages: int
    ) -> tuple[list[LLMMessageResponse], int]:
        """Get recent messages from a conversation."""
        result = await self.db.execute(
            select(LLMMessage)
            .where(LLMMessage.conversation_id == conversation_id)
            .order_by(LLMMessage.created_at.desc())
            .limit(max_messages)
        )
        messages = result.scalars().all()

        # Reverse to get chronological order
        messages = list(reversed(messages))

        total_tokens = sum(m.tokens for m in messages)

        return [LLMMessageResponse.model_validate(m) for m in messages], total_tokens

    def _enhance_prompt(self, base_prompt: str, context_data: dict[str, Any]) -> str:
        """Enhance system prompt with context data."""
        if not context_data or context_data.get("error"):
            return base_prompt

        context_type = context_data.get("type", "unknown")

        if context_type == "audit_case":
            case_info = f"""
Aktueller Kontext: Prüfungsfall
- Projekt: {context_data.get('project_name', 'Unbekannt')}
- Projektnummer: {context_data.get('project_number', 'Unbekannt')}
- Zuwendungsempfänger: {context_data.get('beneficiary', 'Unbekannt')}
- Programm: {context_data.get('program', 'Unbekannt')}
- Status: {context_data.get('status', 'Unbekannt')}
"""
            return f"{base_prompt}\n{case_info}"

        elif context_type == "checklist":
            checklist_info = f"""
Aktueller Kontext: Checkliste
- Name: {context_data.get('name', 'Unbekannt')}
- Projekt: {context_data.get('project_name', 'Unbekannt')}
"""
            return f"{base_prompt}\n{checklist_info}"

        elif context_type == "finding":
            finding_info = f"""
Aktueller Kontext: Feststellung
- Titel: {context_data.get('title', 'Unbekannt')}
- Schweregrad: {context_data.get('severity', 'Unbekannt')}
- Status: {context_data.get('status', 'Unbekannt')}
- Projekt: {context_data.get('project_name', 'Unbekannt')}
"""
            return f"{base_prompt}\n{finding_info}"

        return base_prompt

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: ~4 characters per token for German text
        return len(text) // 4


# API endpoint for context building
async def get_context_for_conversation(
    db: AsyncSession,
    tenant_id: str,
    context_type: str,
    context_id: Optional[str] = None,
    include_history: bool = True,
    max_messages: int = 10,
    conversation_id: Optional[str] = None,
) -> ContextResponse:
    """Get context for a conversation."""
    service = ContextService(db)
    return await service.build_context(
        tenant_id=tenant_id,
        context_type=context_type,
        context_id=context_id,
        include_history=include_history,
        max_messages=max_messages,
        conversation_id=conversation_id,
    )
