from app.models import QuestionOption, QuestionnaireQuestion
from app.schemas import AuditResponseIn
from app.services.scoring import ValidationError, score_responses


def _yes_no_question(qid: int = 1) -> QuestionnaireQuestion:
    q = QuestionnaireQuestion(
        id=qid,
        question_key="Q1_1",
        number_label="1.1",
        title="Test",
        response_type="yes_no_na",
        is_mandatory=True,
        comment_required_when={"equals": "No"},
    )
    q.options = [
        QuestionOption(value="Yes", score=5),
        QuestionOption(value="No", score=0),
        QuestionOption(value="N/A", score=5),
    ]
    return q


def test_score_yes():
    q = _yes_no_question()
    total, mx, _ = score_responses([q], [AuditResponseIn(question_id=1, response_value="Yes")])
    assert total == 5
    assert mx == 5


def test_no_requires_comment():
    q = _yes_no_question()
    try:
        score_responses([q], [AuditResponseIn(question_id=1, response_value="No")])
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert any("comment" in e.lower() for e in exc.details)