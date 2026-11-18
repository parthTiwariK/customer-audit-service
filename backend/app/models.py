from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.db import Base


class UtcDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(DateTime(timezone=True))
        return dialect.type_descriptor(DateTime())

    def process_bind_param(self, value: Optional[datetime], dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        if dialect.name == "postgresql":
            return value
        return value.replace(tzinfo=None)

    def process_result_value(self, value: Optional[datetime], dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class VersionStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class ResponseType(str, enum.Enum):
    yes_no_na = "yes_no_na"
    single_select = "single_select"
    multi_select = "multi_select"
    text = "text"
    rating = "rating"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default=UserRole.user.value)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())


class QuestionnaireTemplate(Base):
    __tablename__ = "questionnaire_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["QuestionnaireVersion"]] = relationship(back_populates="template")


class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_versions"
    __table_args__ = (UniqueConstraint("template_id", "version_number", name="uq_template_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("questionnaire_templates.id", ondelete="RESTRICT"))
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default=VersionStatus.draft.value, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())

    template: Mapped[QuestionnaireTemplate] = relationship(back_populates="versions")
    sections: Mapped[list["QuestionnaireSection"]] = relationship(
        back_populates="version", order_by="QuestionnaireSection.sort_order"
    )


class QuestionnaireSection(Base):
    __tablename__ = "questionnaire_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_versions.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped[QuestionnaireVersion] = relationship(back_populates="sections")
    questions: Mapped[list["QuestionnaireQuestion"]] = relationship(
        back_populates="section", order_by="QuestionnaireQuestion.sort_order"
    )


class QuestionnaireQuestion(Base):
    __tablename__ = "questionnaire_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_sections.id", ondelete="RESTRICT"), index=True
    )
    question_key: Mapped[str] = mapped_column(String(32))
    number_label: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(512))
    criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_type: Mapped[str] = mapped_column(String(32))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    comment_required_when: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scoring_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    section: Mapped[QuestionnaireSection] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(
        back_populates="question", order_by="QuestionOption.sort_order"
    )


class QuestionOption(Base):
    __tablename__ = "questionnaire_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_questions.id", ondelete="RESTRICT"), index=True
    )
    label: Mapped[str] = mapped_column(String(128))
    value: Mapped[str] = mapped_column(String(128))
    score: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[QuestionnaireQuestion] = relationship(back_populates="options")


class Audit(Base):
    __tablename__ = "audits"
    __table_args__ = (
        Index("ix_audits_audit_date", "audit_date"),
        Index("ix_audits_submitted_at", "submitted_at"),
        Index("ix_audits_customer", "customer"),
        Index("ix_audits_tse", "tse"),
        Index("ix_audits_auditor", "auditor"),
        Index("ix_audits_case_priority", "case_priority"),
        Index("ix_audits_customer_tier", "customer_tier"),
        Index("ix_audits_audit_type", "audit_type"),
        Index("ix_audits_total_score", "total_score"),
        Index("ix_audits_questionnaire_version_id", "questionnaire_version_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(128))
    case_id_normalized: Mapped[str] = mapped_column(String(128), unique=True)
    audit_date: Mapped[date] = mapped_column(Date)
    submitted_at: Mapped[datetime] = mapped_column(UtcDateTime())
    customer: Mapped[str] = mapped_column(String(255))
    tse: Mapped[str] = mapped_column(String(255))
    auditor: Mapped[str] = mapped_column(String(255))
    case_priority: Mapped[str] = mapped_column(String(16))
    customer_tier: Mapped[str] = mapped_column(String(32))
    case_status: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    audit_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    questionnaire_version_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_versions.id", ondelete="RESTRICT")
    )
    total_score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer)
    score_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4))
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    areas_for_improvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coaching_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tse_acknowledged: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    submitted_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    responses: Mapped[list["AuditResponse"]] = relationship(back_populates="audit")
    questionnaire_version: Mapped[QuestionnaireVersion] = relationship()


class AuditResponse(Base):
    __tablename__ = "audit_responses"
    __table_args__ = (UniqueConstraint("audit_id", "question_id", name="uq_audit_question"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    audit_id: Mapped[int] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_questions.id", ondelete="RESTRICT"), index=True
    )
    response_value: Mapped[str] = mapped_column(Text)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)

    audit: Mapped[Audit] = relationship(back_populates="responses")
    question: Mapped[QuestionnaireQuestion] = relationship()