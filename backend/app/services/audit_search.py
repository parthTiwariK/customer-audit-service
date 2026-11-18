from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models import Audit

ALLOWED_PAGE_SIZES = {25, 50, 100}
SORT_FIELDS = {
    "audit_date": Audit.audit_date,
    "submitted_at": Audit.submitted_at,
    "score": Audit.total_score,
}


def _utc_start_of_day(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _utc_start_of_next_day(d: date) -> datetime:
    return datetime.combine(d + timedelta(days=1), time.min, tzinfo=timezone.utc)


def search_audits(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 25,
    sort: str = "submitted_at",
    sort_dir: str = "desc",
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
) -> Tuple[List[Audit], int]:
    if page < 1:
        page = 1
    if page_size not in ALLOWED_PAGE_SIZES:
        page_size = 25

    q = select(Audit)
    count_q = select(func.count()).select_from(Audit)

    def apply(stmt):
        if case_id_exact:
            from app.services.scoring import normalize_case_id

            stmt = stmt.where(Audit.case_id_normalized == normalize_case_id(case_id_exact))
        elif case_id and case_id.strip():
            stmt = stmt.where(Audit.case_id.ilike(f"%{case_id.strip()}%"))
        if audit_date_from:
            stmt = stmt.where(Audit.audit_date >= audit_date_from)
        if audit_date_to:
            stmt = stmt.where(Audit.audit_date <= audit_date_to)
        if submitted_from:
            stmt = stmt.where(Audit.submitted_at >= _utc_start_of_day(submitted_from))
        if submitted_to:
            stmt = stmt.where(Audit.submitted_at < _utc_start_of_next_day(submitted_to))
        if customer and customer.strip():
            stmt = stmt.where(Audit.customer.ilike(f"%{customer.strip()}%"))
        if tse and tse.strip():
            stmt = stmt.where(Audit.tse.ilike(f"%{tse.strip()}%"))
        if auditor and auditor.strip():
            stmt = stmt.where(Audit.auditor.ilike(f"%{auditor.strip()}%"))
        if case_priority:
            stmt = stmt.where(Audit.case_priority == case_priority)
        if customer_tier:
            stmt = stmt.where(Audit.customer_tier == customer_tier)
        if case_status and case_status.strip():
            stmt = stmt.where(Audit.case_status.ilike(f"%{case_status.strip()}%"))
        if audit_type and audit_type.strip():
            stmt = stmt.where(Audit.audit_type.ilike(f"%{audit_type.strip()}%"))
        if score_min is not None:
            stmt = stmt.where(Audit.total_score >= score_min)
        if score_max is not None:
            stmt = stmt.where(Audit.total_score <= score_max)
        return stmt

    q = apply(q)
    count_q = apply(count_q)

    col = SORT_FIELDS.get(sort, Audit.submitted_at)
    order = desc(col) if sort_dir.lower() != "asc" else asc(col)
    q = q.order_by(order, desc(Audit.id))

    total = db.scalar(count_q) or 0
    rows = db.scalars(q.offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), int(total)