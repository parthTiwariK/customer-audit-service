from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models import QuestionnaireQuestion, QuestionnaireSection, QuestionnaireVersion
from app.schemas import AuditResponseIn


class ValidationError(Exception):
    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message)
        self.details = details or [message]


def normalize_case_id(case_id: str) -> str:
    return case_id.strip().upper()


def load_version_questions(db: Session, version_id: int) -> list[QuestionnaireQuestion]:
    version = (
        db.query(QuestionnaireVersion)
        .options(
            joinedload(QuestionnaireVersion.sections)
            .joinedload(QuestionnaireSection.questions)
            .joinedload(QuestionnaireQuestion.options)
        )
        .filter(QuestionnaireVersion.id == version_id)
        .one_or_none()
    )
    if not version:
        raise ValidationError("Questionnaire version not found")
    questions: list[QuestionnaireQuestion] = []
    for section in sorted(version.sections, key=lambda s: s.sort_order):
        for q in sorted(section.questions, key=lambda x: x.sort_order):
            questions.append(q)
    return questions


def score_responses(
    questions: list[QuestionnaireQuestion],
    responses: list[AuditResponseIn],
) -> Tuple[int, int, List[Tuple[QuestionnaireQuestion, str, Optional[str], int]]]:
    by_id = {q.id: q for q in questions}
    provided = {r.question_id: r for r in responses}
    errors: list[str] = []
    scored: List[Tuple[QuestionnaireQuestion, str, Optional[str], int]] = []
    total = 0
    max_score = 0

    for question in questions:
        max_score += _max_points(question)
        resp = provided.get(question.id)
        if question.is_mandatory and not resp:
            errors.append(f"{question.number_label}: rating required")
            continue
        if not resp:
            continue
        value = resp.response_value.strip()
        if not value:
            errors.append(f"{question.number_label}: rating required")
            continue
        comment = (resp.comment or "").strip() or None
        if _comment_required(question, value) and not comment:
            errors.append(f"{question.number_label}: comment required for {value}")
            continue
        points = _points_for(question, value)
        if points is None:
            errors.append(f"{question.number_label}: invalid response {value!r}")
            continue
        total += points
        scored.append((question, value, comment, points))

    extra_ids = set(provided) - set(by_id)
    for qid in extra_ids:
        errors.append(f"Unknown question id {qid}")

    if errors:
        raise ValidationError("Validation failed", errors)

    return total, max_score, scored


def _max_points(question: QuestionnaireQuestion) -> int:
    if question.options:
        return max(o.score for o in question.options)
    if question.scoring_config and "max" in question.scoring_config:
        return int(question.scoring_config["max"])
    return 5 if question.response_type == "yes_no_na" else 0


def _comment_required(question: QuestionnaireQuestion, value: str) -> bool:
    rule = question.comment_required_when or {}
    if "equals" in rule:
        return value == rule["equals"]
    return False


def _points_for(question: QuestionnaireQuestion, value: str) -> Optional[int]:
    for opt in question.options:
        if opt.value == value:
            return opt.score
    if question.response_type == "rating":
        try:
            n = int(value)
        except ValueError:
            return None
        cfg = question.scoring_config or {}
        if cfg.get("per_point"):
            return n * int(cfg["per_point"])
        return n
    return None


def score_pct(total: int, max_score: int) -> Decimal:
    if max_score <= 0:
        return Decimal("0")
    return (Decimal(total) / Decimal(max_score)).quantize(Decimal("0.0001"))