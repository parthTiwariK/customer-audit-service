from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import CurrentUser
from app.db import get_db
from app.models import Audit, AuditResponse, QuestionnaireQuestion, QuestionnaireVersion
from app.schemas import (
    AuditDetailOut,
    AuditListItem,
    AuditSearchResult,
    AuditSubmitIn,
    CaseExistsOut,
)
from app.services.audit_search import search_audits
from app.services.scoring import (
    ValidationError,
    load_version_questions,
    normalize_case_id,
    score_pct,
    score_responses,
)

router = APIRouter(prefix="/api/v1", tags=["audits"])


@router.get("/audits", response_model=AuditSearchResult)
def list_audits(
    _user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25),
    sort: str = Query("submitted_at"),
    sort_dir: str = Query("desc"),
    case_id: Optional[str] = None,
    case_id_exact: Optional[str] = None,
    audit_date_from: Optional[date] = None,
    audit_date_to: Optional[date] = None,
    submitted_from: Optional[date] = None,
    submitted_to: Optional[date] = None,
    customer: Optional[str] = None,
    tse: Optional[str] = None,
    auditor: Optional[str] = None,
    case_priority: Optional[str] = None,
    customer_tier: Optional[str] = None,
    case_status: Optional[str] = None,
    audit_type: Optional[str] = None,
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
):
    rows, total = search_audits(
        db,
        page=page,
        page_size=page_size,
        sort=sort,
        sort_dir=sort_dir,
        case_id=case_id,
        case_id_exact=case_id_exact,
        audit_date_from=audit_date_from,
        audit_date_to=audit_date_to,
        submitted_from=submitted_from,
        submitted_to=submitted_to,
        customer=customer,
        tse=tse,
        auditor=auditor,
        case_priority=case_priority,
        customer_tier=customer_tier,
        case_status=case_status,
        audit_type=audit_type,
        score_min=score_min,
        score_max=score_max,
    )
    return AuditSearchResult(
        items=[AuditListItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size if page_size in (25, 50, 100) else 25,
    )


@router.get("/audits/case/{case_id}/exists", response_model=CaseExistsOut)
def case_exists(case_id: str, _user: CurrentUser, db: Session = Depends(get_db)):
    norm = normalize_case_id(case_id)
    audit = db.query(Audit).filter(Audit.case_id_normalized == norm).one_or_none()
    return CaseExistsOut(exists=audit is not None, audit_id=audit.id if audit else None)


@router.get("/audits/{audit_id}", response_model=AuditDetailOut)
def get_audit(audit_id: int, _user: CurrentUser, db: Session = Depends(get_db)):
    audit = (
        db.query(Audit)
        .options(
            joinedload(Audit.questionnaire_version).joinedload(QuestionnaireVersion.template),
            joinedload(Audit.responses)
            .joinedload(AuditResponse.question)
            .joinedload(QuestionnaireQuestion.section),
        )
        .filter(Audit.id == audit_id)
        .one_or_none()
    )
    if not audit:
        raise HTTPException(404, "Audit not found")

    response_rows = []
    for r in audit.responses:
        q: QuestionnaireQuestion = r.question
        response_rows.append(
            {
                "question_id": r.question_id,
                "question_key": q.question_key,
                "number_label": q.number_label,
                "title": q.title,
                "section_title": q.section.title if q.section else "",
                "response_value": r.response_value,
                "comment": r.comment,
                "points_earned": r.points_earned,
            }
        )
    response_rows.sort(key=lambda x: x["number_label"])

    return AuditDetailOut(
        id=audit.id,
        case_id=audit.case_id,
        audit_date=audit.audit_date,
        submitted_at=audit.submitted_at,
        customer=audit.customer,
        tse=audit.tse,
        auditor=audit.auditor,
        case_priority=audit.case_priority,
        customer_tier=audit.customer_tier,
        case_status=audit.case_status,
        audit_type=audit.audit_type,
        questionnaire_version_id=audit.questionnaire_version_id,
        template_name=audit.questionnaire_version.template.name,
        version_number=audit.questionnaire_version.version_number,
        total_score=audit.total_score,
        max_score=audit.max_score,
        score_pct=audit.score_pct,
        strengths=audit.strengths,
        areas_for_improvement=audit.areas_for_improvement,
        coaching_action=audit.coaching_action,
        tse_acknowledged=audit.tse_acknowledged,
        responses=response_rows,
    )


@router.post("/audits", response_model=AuditDetailOut, status_code=201)
def submit_audit(payload: AuditSubmitIn, user: CurrentUser, db: Session = Depends(get_db)):
    version = db.get(QuestionnaireVersion, payload.questionnaire_version_id)
    if not version:
        raise HTTPException(400, "Invalid questionnaire version")
    if version.status != "published":
        raise HTTPException(400, "Only published questionnaire versions can be used")

    norm = normalize_case_id(payload.case_id)
    if db.query(Audit).filter(Audit.case_id_normalized == norm).first():
        raise HTTPException(409, "An audit already exists for this Case ID")

    try:
        questions = load_version_questions(db, payload.questionnaire_version_id)
        total, max_score, scored = score_responses(questions, payload.responses)
    except ValidationError as exc:
        raise HTTPException(422, detail={"message": str(exc), "errors": exc.details}) from exc

    now = datetime.now(timezone.utc)
    audit = Audit(
        case_id=payload.case_id.strip(),
        case_id_normalized=norm,
        audit_date=payload.audit_date,
        submitted_at=now,
        customer=payload.customer.strip(),
        tse=payload.tse.strip(),
        auditor=payload.auditor.strip(),
        case_priority=payload.case_priority,
        customer_tier=payload.customer_tier,
        case_status=(payload.case_status or "").strip() or None,
        audit_type=(payload.audit_type or "").strip() or None,
        questionnaire_version_id=payload.questionnaire_version_id,
        total_score=total,
        max_score=max_score,
        score_pct=score_pct(total, max_score),
        strengths=payload.strengths,
        areas_for_improvement=payload.areas_for_improvement,
        coaching_action=payload.coaching_action,
        tse_acknowledged=payload.tse_acknowledged,
        submitted_by_user_id=user.id,
    )
    db.add(audit)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "An audit already exists for this Case ID") from exc

    for question, value, comment, points in scored:
        db.add(
            AuditResponse(
                audit_id=audit.id,
                question_id=question.id,
                response_value=value,
                comment=comment,
                points_earned=points,
            )
        )
    db.commit()
    return get_audit(audit.id, user, db)