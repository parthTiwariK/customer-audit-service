from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.db import get_db
from app.models import Audit
from app.schemas import DashboardSummaryOut

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.get("/reports/summary", response_model=DashboardSummaryOut)
def dashboard_summary(
    _user: CurrentUser,
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None, alias="from"),
    date_to: Optional[date] = Query(None, alias="to"),
):
    base = db.query(Audit)
    if date_from:
        base = base.filter(Audit.audit_date >= date_from)
    if date_to:
        base = base.filter(Audit.audit_date <= date_to)

    count = base.count()
    avg = db.query(func.avg(Audit.score_pct)).select_from(Audit)
    if date_from:
        avg = avg.filter(Audit.audit_date >= date_from)
    if date_to:
        avg = avg.filter(Audit.audit_date <= date_to)
    avg_val = float(avg.scalar() or 0)

    def grouped(col):
        q = db.query(col, func.count(Audit.id), func.avg(Audit.score_pct))
        if date_from:
            q = q.filter(Audit.audit_date >= date_from)
        if date_to:
            q = q.filter(Audit.audit_date <= date_to)
        rows = q.group_by(col).order_by(func.count(Audit.id).desc()).limit(20).all()
        return [
            {"name": r[0], "count": int(r[1]), "avg_score_pct": round(float(r[2] or 0) * 100, 1)}
            for r in rows
        ]

    return DashboardSummaryOut(
        audit_count=count,
        avg_score_pct=round(avg_val * 100, 1),
        by_auditor=grouped(Audit.auditor),
        by_tse=grouped(Audit.tse),
        by_customer_tier=grouped(Audit.customer_tier),
    )