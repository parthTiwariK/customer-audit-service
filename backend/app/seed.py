import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    QuestionOption,
    QuestionnaireQuestion,
    QuestionnaireSection,
    QuestionnaireTemplate,
    QuestionnaireVersion,
    VersionStatus,
)


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "case_quality_audit_v1.json"


def seed_if_empty(db: Session) -> None:
    existing = db.query(QuestionnaireTemplate).filter(QuestionnaireTemplate.slug == "case-quality-audit").first()
    if existing:
        return

    raw = json.loads(_seed_path().read_text(encoding="utf-8"))
    tpl_meta = raw["template"]
    template = QuestionnaireTemplate(
        name=tpl_meta["name"],
        slug=tpl_meta["slug"],
        description=tpl_meta.get("description"),
    )
    db.add(template)
    db.flush()

    version = QuestionnaireVersion(
        template_id=template.id,
        version_number=raw.get("version_number", 1),
        status=VersionStatus.published.value,
        published_at=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()

    for sec_data in raw["sections"]:
        section = QuestionnaireSection(
            version_id=version.id,
            title=sec_data["title"],
            sort_order=sec_data.get("sort_order", 0),
        )
        db.add(section)
        db.flush()
        for qi, q_data in enumerate(sec_data["questions"]):
            question = QuestionnaireQuestion(
                section_id=section.id,
                question_key=q_data["question_key"],
                number_label=q_data["number_label"],
                title=q_data["title"],
                criteria=q_data.get("criteria"),
                response_type=q_data["response_type"],
                is_mandatory=True,
                comment_required_when=q_data.get("comment_required_when"),
                scoring_config=q_data.get("scoring_config"),
                sort_order=q_data.get("sort_order", qi),
            )
            db.add(question)
            db.flush()
            for oi, opt in enumerate(q_data.get("options", [])):
                db.add(
                    QuestionOption(
                        question_id=question.id,
                        label=opt["label"],
                        value=opt["value"],
                        score=opt["score"],
                        sort_order=oi,
                    )
                )
    db.commit()