"""History API Endpoints for Workflow-Historisierung (Feature 7).

AC-7.1.1: Events werden geloggt
AC-7.1.2: Konversationen werden gespeichert
AC-7.1.3: Feedback kann hinzugefuegt werden
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.history import (
    ModuleEvent,
    LLMConversation,
    LLMMessage,
    LLMFeedback,
    EventType,
    FeedbackType,
)
from app.schemas.history import (
    ModuleEventCreate,
    ModuleEventResponse,
    ModuleEventListResponse,
    LLMConversationCreate,
    LLMConversationUpdate,
    LLMConversationResponse,
    LLMConversationListResponse,
    LLMConversationWithMessagesResponse,
    LLMMessageCreate,
    LLMMessageResponse,
    LLMMessageListResponse,
    LLMFeedbackCreate,
    LLMFeedbackResponse,
    LLMFeedbackListResponse,
    ContextRequest,
    ContextResponse,
)
from app.core.context_service import ContextService

router = APIRouter()


# --- Module Events (AC-7.1.1) ---


@router.get("/events", response_model=ModuleEventListResponse)
async def list_module_events(
    module_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    event_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List module events with filtering."""
    query = select(ModuleEvent)

    if module_id:
        query = query.where(ModuleEvent.module_id == module_id)
    if customer_id:
        query = query.where(ModuleEvent.customer_id == customer_id)
    if event_type:
        query = query.where(ModuleEvent.event_type == event_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(ModuleEvent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    return ModuleEventListResponse(
        items=[ModuleEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/events", response_model=ModuleEventResponse, status_code=201)
async def create_module_event(
    data: ModuleEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a module event (AC-7.1.1)."""
    event = ModuleEvent(
        id=str(uuid4()),
        module_id=data.module_id,
        customer_id=data.customer_id,
        event_type=EventType(data.event_type),
        version=data.version,
        previous_version=data.previous_version,
        user_id=data.user_id or current_user.id,
        details=data.details,
        error_message=data.error_message,
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return ModuleEventResponse.model_validate(event)


@router.get("/events/{event_id}", response_model=ModuleEventResponse)
async def get_module_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific module event."""
    result = await db.execute(select(ModuleEvent).where(ModuleEvent.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return ModuleEventResponse.model_validate(event)


# --- LLM Conversations (AC-7.1.2) ---


@router.get("/conversations", response_model=LLMConversationListResponse)
async def list_conversations(
    context_type: Optional[str] = None,
    context_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List LLM conversations for current tenant."""
    query = select(LLMConversation).where(
        LLMConversation.tenant_id == current_user.tenant_id
    )

    if context_type:
        query = query.where(LLMConversation.context_type == context_type)
    if context_id:
        query = query.where(LLMConversation.context_id == context_id)
    if is_active is not None:
        query = query.where(LLMConversation.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(LLMConversation.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return LLMConversationListResponse(
        items=[LLMConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/conversations", response_model=LLMConversationResponse, status_code=201)
async def create_conversation(
    data: LLMConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new LLM conversation (AC-7.1.2)."""
    conversation = LLMConversation(
        id=str(uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        context_type=data.context_type,
        context_id=data.context_id,
        title=data.title,
        model_used=data.model_used,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return LLMConversationResponse.model_validate(conversation)


@router.get(
    "/conversations/{conversation_id}",
    response_model=LLMConversationWithMessagesResponse,
)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a conversation with all messages."""
    result = await db.execute(
        select(LLMConversation)
        .where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
        .options(
            selectinload(LLMConversation.messages),
            selectinload(LLMConversation.feedbacks),
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return LLMConversationWithMessagesResponse.model_validate(conversation)


@router.patch(
    "/conversations/{conversation_id}", response_model=LLMConversationResponse
)
async def update_conversation(
    conversation_id: str,
    data: LLMConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a conversation."""
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if data.title is not None:
        conversation.title = data.title
    if data.is_active is not None:
        conversation.is_active = data.is_active

    conversation.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(conversation)

    return LLMConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()


# --- LLM Messages ---


@router.get(
    "/conversations/{conversation_id}/messages", response_model=LLMMessageListResponse
)
async def list_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List messages for a conversation."""
    # Verify conversation access
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(LLMMessage)
        .where(LLMMessage.conversation_id == conversation_id)
        .order_by(LLMMessage.created_at)
    )
    messages = result.scalars().all()

    return LLMMessageListResponse(
        items=[LLMMessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=LLMMessageResponse,
    status_code=201,
)
async def add_message(
    conversation_id: str,
    data: LLMMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a message to a conversation."""
    # Verify conversation access
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = LLMMessage(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role=data.role,
        content=data.content,
        tokens=data.tokens,
        extra_data=data.extra_data,
    )

    # Update conversation token count
    conversation.total_tokens += data.tokens
    conversation.updated_at = datetime.now(timezone.utc)

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return LLMMessageResponse.model_validate(message)


# --- LLM Feedback (AC-7.1.3) ---


@router.get(
    "/conversations/{conversation_id}/feedback", response_model=LLMFeedbackListResponse
)
async def list_feedback(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List feedback for a conversation."""
    # Verify conversation access
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(LLMFeedback)
        .where(LLMFeedback.conversation_id == conversation_id)
        .order_by(LLMFeedback.created_at.desc())
    )
    feedbacks = result.scalars().all()

    return LLMFeedbackListResponse(
        items=[LLMFeedbackResponse.model_validate(f) for f in feedbacks],
        total=len(feedbacks),
    )


@router.post(
    "/conversations/{conversation_id}/feedback",
    response_model=LLMFeedbackResponse,
    status_code=201,
)
async def add_feedback(
    conversation_id: str,
    data: LLMFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add feedback to a conversation (AC-7.1.3)."""
    # Verify conversation access
    result = await db.execute(
        select(LLMConversation).where(
            LLMConversation.id == conversation_id,
            LLMConversation.tenant_id == current_user.tenant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify message belongs to conversation if provided
    if data.message_id:
        result = await db.execute(
            select(LLMMessage).where(
                LLMMessage.id == data.message_id,
                LLMMessage.conversation_id == conversation_id,
            )
        )
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

    feedback = LLMFeedback(
        id=str(uuid4()),
        conversation_id=conversation_id,
        message_id=data.message_id,
        user_id=current_user.id,
        feedback_type=FeedbackType(data.feedback_type),
        comment=data.comment,
        rating=data.rating,
    )

    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return LLMFeedbackResponse.model_validate(feedback)


# --- Utility Functions ---


async def log_module_event(
    db: AsyncSession,
    module_id: str,
    customer_id: str,
    event_type: EventType,
    version: Optional[str] = None,
    previous_version: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
    error_message: Optional[str] = None,
) -> ModuleEvent:
    """Utility function to log a module event."""
    event = ModuleEvent(
        id=str(uuid4()),
        module_id=module_id,
        customer_id=customer_id,
        event_type=event_type,
        version=version,
        previous_version=previous_version,
        user_id=user_id,
        details=details,
        error_message=error_message,
    )
    db.add(event)
    return event


# --- Context Building (AC-7.1.4) ---


@router.post("/context", response_model=ContextResponse)
async def build_context(
    data: ContextRequest,
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Build context for LLM conversation (AC-7.1.4)."""
    service = ContextService(db)
    return await service.build_context(
        tenant_id=current_user.tenant_id,
        context_type=data.context_type,
        context_id=data.context_id,
        include_history=data.include_history,
        max_messages=data.max_messages,
        conversation_id=conversation_id,
    )
