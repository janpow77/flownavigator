"""History models for Workflow-Historisierung (Feature 7)."""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class EventType(str, PyEnum):
    """Module event types."""

    installed = "installed"
    updated = "updated"
    uninstalled = "uninstalled"
    configured = "configured"
    error = "error"
    started = "started"
    completed = "completed"


class FeedbackType(str, PyEnum):
    """LLM feedback types."""

    helpful = "helpful"
    not_helpful = "not_helpful"
    partially_helpful = "partially_helpful"
    incorrect = "incorrect"


class ModuleEvent(Base):
    """Module event history.

    AC-7.1.1: Events werden geloggt
    """

    __tablename__ = "module_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    module_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"),
        nullable=False,
    )
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    previous_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class LLMConversation(Base, TimestampMixin):
    """LLM conversation session.

    AC-7.1.2: Konversationen werden gespeichert
    """

    __tablename__ = "llm_conversations"

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
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    context_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., "audit_case", "checklist", "finding"
    context_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    messages: Mapped[list["LLMMessage"]] = relationship(
        "LLMMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="LLMMessage.created_at",
    )
    feedbacks: Mapped[list["LLMFeedback"]] = relationship(
        "LLMFeedback",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class LLMMessage(Base):
    """LLM message in a conversation."""

    __tablename__ = "llm_messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("llm_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", "system", name="message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["LLMConversation"] = relationship(
        "LLMConversation",
        back_populates="messages",
    )


class LLMFeedback(Base):
    """User feedback on LLM responses.

    AC-7.1.3: Feedback kann hinzugefügt werden
    """

    __tablename__ = "llm_feedbacks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("llm_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("llm_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType, name="feedback_type"),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["LLMConversation"] = relationship(
        "LLMConversation",
        back_populates="feedbacks",
    )
