"""PostgreSQL persistence models for Zyntrix Phase 4A AI Engineering Copilot.

Includes:
- AIConversation: Multi-tenant conversation container
- AIMessage: Dialogue turns with structured payloads and citations
- AIExecution: LangGraph execution trace and state snapshots
- AIToolCall: Tool execution traces
- AIActionProposal: Human-gated proposals for mutations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Text, ForeignKey, JSON, Integer, Float, Boolean, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from backend.app.models.base import Base


class AIConversation(Base):
    """Multi-tenant, job-scoped container for conversational assistant sessions."""

    __tablename__ = "ai_conversations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="Engineering Copilot Session", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at")
    executions = relationship("AIExecution", back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(Base):
    """Individual dialogue turn in an AI conversation."""

    __tablename__ = "ai_messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Structured response payload: claims, sources, suggested_actions, authority_level
    structured_payload: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
    
    # Model telemetry (NO CREDENTIALS)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    conversation = relationship("AIConversation", back_populates="messages")


class AIExecution(Base):
    """LangGraph execution record tracking state machine progression."""

    __tablename__ = "ai_executions"

    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    intent: Mapped[str] = mapped_column(String(100), default="INFORMATIONAL", nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), default="ORCHESTRATOR", nullable=False)
    
    # Immutable snapshot of LangGraph state (without sensitive tokens)
    state_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)  # COMPLETED | FAILED | REJECTED_BY_FIREWALL
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    conversation = relationship("AIConversation", back_populates="executions")
    tool_calls = relationship("AIToolCall", back_populates="execution", cascade="all, delete-orphan")


class AIToolCall(Base):
    """Audit log of individual tool invocations made during LangGraph execution."""

    __tablename__ = "ai_tool_calls"

    execution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    execution = relationship("AIExecution", back_populates="tool_calls")


class AIActionProposal(Base):
    """Human-gated proposal created by AI requiring explicit user confirmation.
    
    AI has zero mutation authority. Every mutation must go through an ActionProposal.
    """

    __tablename__ = "ai_action_proposals"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Proposal classification: CREATE_REVIEW_REQUEST | CREATE_DNA_CANDIDATE | MAP_REQUIREMENT
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    proposal_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    
    # Status: PROPOSED | CONFIRMED | REJECTED
    status: Mapped[str] = mapped_column(String(50), default="PROPOSED", nullable=False, index=True)
    
    created_by_agent: Mapped[str] = mapped_column(String(100), default="AI_ENGINEERING_COPILOT", nullable=False)
    confirmed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
