from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.auth import CurrentUser
from app.db import get_db
from app.models import (
    QuestionnaireQuestion,
    QuestionnaireSection,
    QuestionnaireTemplate,
    QuestionnaireVersion,
    VersionStatus,
)
from app.schemas import QuestionnaireVersionOut, SectionOut

router = APIRouter(prefix="/api/v1", tags=["questionnaires"])


def _version_graph(db: Session, version: QuestionnaireVersion) -> QuestionnaireVersionOut:
    version = (
        db.query(QuestionnaireVersion)
        .options(
            joinedload(QuestionnaireVersion.template),
            joinedload(QuestionnaireVersion.sections)
            .joinedload(QuestionnaireSection.questions)
            .joinedload(QuestionnaireQuestion.options),
        )
        .filter(QuestionnaireVersion.id == version.id)
        .one()
    )
    sections = []
    for sec in sorted(version.sections, key=lambda s: s.sort_order):
        questions = []
        for q in sorted(sec.questions, key=lambda x: x.sort_order):
            questions.append(
                {
                    "id": q.id,
                    "question_key": q.question_key,
                    "number_label": q.number_label,
                    "title": q.title,
                    "criteria": q.criteria,
                    "response_type": q.response_type,
                    "is_mandatory": q.is_mandatory,
                    "comment_required_when": q.comment_required_when,
                    "sort_order": q.sort_order,
                    "options": sorted(q.options, key=lambda o: o.sort_order),
                }
            )
        sections.append(SectionOut(id=sec.id, title=sec.title, sort_order=sec.sort_order, questions=questions))
    return QuestionnaireVersionOut(
        id=version.id,
        template_id=version.template_id,
        template_name=version.template.name,
        template_slug=version.template.slug,
        version_number=version.version_number,
        status=version.status,
        sections=sections,
    )


@router.get("/questionnaires/latest", response_model=list[QuestionnaireVersionOut])
def latest_questionnaires(_user: CurrentUser, db: Session = Depends(get_db)):
    templates = db.query(QuestionnaireTemplate).order_by(QuestionnaireTemplate.name).all()
    out: list[QuestionnaireVersionOut] = []
    for tpl in templates:
        version = (
            db.query(QuestionnaireVersion)
            .filter(
                QuestionnaireVersion.template_id == tpl.id,
                QuestionnaireVersion.status == VersionStatus.published.value,
            )
            .order_by(desc(QuestionnaireVersion.version_number))
            .first()
        )
        if version:
            out.append(_version_graph(db, version))
    return out


@router.get("/questionnaires/versions/{version_id}", response_model=QuestionnaireVersionOut)
def get_version(version_id: int, _user: CurrentUser, db: Session = Depends(get_db)):
    version = db.get(QuestionnaireVersion, version_id)
    if not version:
        raise HTTPException(404, "Version not found")
    return _version_graph(db, version)