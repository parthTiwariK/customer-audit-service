from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: str

    model_config = {"from_attributes": True}


class LocalLoginIn(BaseModel):
    username: str
    password: str


class QuestionOptionOut(BaseModel):
    id: int
    label: str
    value: str
    score: int
    sort_order: int

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    question_key: str
    number_label: str
    title: str
    criteria: Optional[str] = None
    response_type: str
    is_mandatory: bool
    comment_required_when: Optional[Dict[str, Any]] = None
    sort_order: int
    options: List[QuestionOptionOut] = []

    model_config = {"from_attributes": True}


class SectionOut(BaseModel):
    id: int
    title: str
    sort_order: int
    questions: List[QuestionOut] = []

    model_config = {"from_attributes": True}


class QuestionnaireVersionOut(BaseModel):
    id: int
    template_id: int
    template_name: str
    template_slug: str
    version_number: int
    status: str
    sections: List[SectionOut] = []


class AuditListItem(BaseModel):
    id: int
    case_id: str
    customer: str
    tse: str
    auditor: str
    case_priority: str
    customer_tier: str
    audit_type: Optional[str] = None
    audit_date: date
    total_score: int
    max_score: int
    score_pct: Decimal
    submitted_at: datetime

    model_config = {"from_attributes": True}


class AuditSearchResult(BaseModel):
    items: List[AuditListItem]
    total: int
    page: int
    page_size: int


class AuditResponseIn(BaseModel):
    question_id: int
    response_value: str
    comment: Optional[str] = None


class AuditSubmitIn(BaseModel):
    case_id: str
    audit_date: date
    auditor: str
    tse: str
    customer: str
    case_priority: str
    customer_tier: str
    case_status: Optional[str] = None
    audit_type: Optional[str] = None
    questionnaire_version_id: int
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    coaching_action: Optional[str] = None
    tse_acknowledged: Optional[str] = None
    responses: List[AuditResponseIn]


class AuditResponseOut(BaseModel):
    question_id: int
    question_key: str
    number_label: str
    title: str
    section_title: str
    response_value: str
    comment: Optional[str] = None
    points_earned: int


class AuditDetailOut(BaseModel):
    id: int
    case_id: str
    audit_date: date
    submitted_at: datetime
    customer: str
    tse: str
    auditor: str
    case_priority: str
    customer_tier: str
    case_status: Optional[str] = None
    audit_type: Optional[str] = None
    questionnaire_version_id: int
    template_name: str
    version_number: int
    total_score: int
    max_score: int
    score_pct: Decimal
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    coaching_action: Optional[str] = None
    tse_acknowledged: Optional[str] = None
    responses: List[AuditResponseOut]


class CaseExistsOut(BaseModel):
    exists: bool
    audit_id: Optional[int] = None


class DashboardSummaryOut(BaseModel):
    audit_count: int
    avg_score_pct: float
    by_auditor: List[Dict[str, Any]]
    by_tse: List[Dict[str, Any]]
    by_customer_tier: List[Dict[str, Any]]