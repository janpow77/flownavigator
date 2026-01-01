"""History schemas for Workflow-Historisierung (Feature 7)."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Module event types."""

    installed = "installed"
    updated = "updated"
    uninstalled = "uninstalled"
    configured = "configured"
    error = "error"
    started = "started"
    completed = "completed"


class FeedbackType(str, Enum):
    """LLM feedback types."""

    helpful = "helpful"
    not_helpful = "not_helpful"
    partially_helpful = "partially_helpful"
    incorrect = "incorrect"


# Module Event Schemas
class ModuleEventCreate(BaseModel):
    """Create module event."""

    module_id: str
    customer_id: str
    event_type: EventType
    version: Optional[str] = None
    previous_version: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class ModuleEventResponse(BaseModel):
    """Module event response."""

    id: str
    module_id: str
    customer_id: str
    event_type: EventType
    version: Optional[str] = None
    previous_version: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModuleEventListResponse(BaseModel):
    """Module events list response."""

    items: list[ModuleEventResponse]
    total: int
    page: int = 1
    page_size: int = 20


# LLM Conversation Schemas
class LLMConversationCreate(BaseModel):
    """Create LLM conversation."""

    context_type: str = Field(..., max_length=50)
    context_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    model_used: Optional[str] = Field(None, max_length=100)


class LLMConversationUpdate(BaseModel):
    """Update LLM conversation."""

    title: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class LLMConversationResponse(BaseModel):
    """LLM conversation response."""

    id: str
    tenant_id: str
    user_id: Optional[str] = None
    context_type: str
    context_id: Optional[str] = None
    title: Optional[str] = None
    model_used: Optional[str] = None
    total_tokens: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LLMConversationListResponse(BaseModel):
    """LLM conversations list response."""

    items: list[LLMConversationResponse]
    total: int
    page: int = 1
    page_size: int = 20


# LLM Message Schemas
class LLMMessageCreate(BaseModel):
    """Create LLM message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    tokens: int = 0
    extra_data: Optional[dict[str, Any]] = None


class LLMMessageResponse(BaseModel):
    """LLM message response."""

    id: str
    conversation_id: str
    role: str
    content: str
    tokens: int
    extra_data: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMMessageListResponse(BaseModel):
    """LLM messages list response."""

    items: list[LLMMessageResponse]
    total: int


# LLM Feedback Schemas
class LLMFeedbackCreate(BaseModel):
    """Create LLM feedback (AC-7.1.3)."""

    message_id: Optional[str] = None
    feedback_type: FeedbackType
    comment: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


class LLMFeedbackResponse(BaseModel):
    """LLM feedback response."""

    id: str
    conversation_id: str
    message_id: Optional[str] = None
    user_id: Optional[str] = None
    feedback_type: FeedbackType
    comment: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMFeedbackListResponse(BaseModel):
    """LLM feedbacks list response."""

    items: list[LLMFeedbackResponse]
    total: int


# Conversation with messages
class LLMConversationWithMessagesResponse(BaseModel):
    """Conversation with all messages."""

    id: str
    tenant_id: str
    user_id: Optional[str] = None
    context_type: str
    context_id: Optional[str] = None
    title: Optional[str] = None
    model_used: Optional[str] = None
    total_tokens: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: list[LLMMessageResponse]
    feedbacks: list[LLMFeedbackResponse]

    model_config = {"from_attributes": True}


# Context building (AC-7.1.4)
class ContextRequest(BaseModel):
    """Request for context building."""

    context_type: str
    context_id: Optional[str] = None
    include_history: bool = True
    max_messages: int = Field(default=10, ge=1, le=100)


class ContextResponse(BaseModel):
    """Built context for LLM."""

    system_prompt: str
    context_data: dict[str, Any]
    recent_messages: list[LLMMessageResponse]
    total_context_tokens: int
