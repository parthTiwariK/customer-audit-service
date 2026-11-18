"""mysql baseline schema

Revision ID: 001
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def _now():
    return sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=_now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "questionnaire_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=_now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=_now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_questionnaire_templates_slug"),
    )
    op.create_index("ix_questionnaire_templates_slug", "questionnaire_templates", ["slug"])

    op.create_table(
        "questionnaire_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("questionnaire_templates.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=_now(), nullable=False),
        sa.UniqueConstraint("template_id", "version_number", name="uq_template_version"),
    )
    op.create_index("ix_questionnaire_versions_status", "questionnaire_versions", ["status"])

    op.create_table(
        "questionnaire_sections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("questionnaire_versions.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_questionnaire_sections_version_id", "questionnaire_sections", ["version_id"])

    op.create_table(
        "questionnaire_questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("questionnaire_sections.id"), nullable=False),
        sa.Column("question_key", sa.String(32), nullable=False),
        sa.Column("number_label", sa.String(16), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("criteria", sa.Text(), nullable=True),
        sa.Column("response_type", sa.String(32), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("comment_required_when", sa.JSON(), nullable=True),
        sa.Column("scoring_config", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_questionnaire_questions_section_id", "questionnaire_questions", ["section_id"])

    op.create_table(
        "questionnaire_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questionnaire_questions.id"), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("value", sa.String(128), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_questionnaire_options_question_id", "questionnaire_options", ["question_id"])

    op.create_table(
        "audits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.String(128), nullable=False),
        sa.Column("case_id_normalized", sa.String(128), nullable=False),
        sa.Column("audit_date", sa.Date(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("customer", sa.String(255), nullable=False),
        sa.Column("tse", sa.String(255), nullable=False),
        sa.Column("auditor", sa.String(255), nullable=False),
        sa.Column("case_priority", sa.String(16), nullable=False),
        sa.Column("customer_tier", sa.String(32), nullable=False),
        sa.Column("case_status", sa.String(128), nullable=True),
        sa.Column("audit_type", sa.String(128), nullable=True),
        sa.Column("questionnaire_version_id", sa.Integer(), sa.ForeignKey("questionnaire_versions.id"), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("score_pct", sa.Numeric(7, 4), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("areas_for_improvement", sa.Text(), nullable=True),
        sa.Column("coaching_action", sa.Text(), nullable=True),
        sa.Column("tse_acknowledged", sa.String(16), nullable=True),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("case_id_normalized", name="uq_audits_case_id_normalized"),
    )
    op.create_index("ix_audits_submitted_at", "audits", ["submitted_at"])
    op.create_index("ix_audits_audit_date", "audits", ["audit_date"])
    op.create_index("ix_audits_customer", "audits", ["customer"])
    op.create_index("ix_audits_tse", "audits", ["tse"])
    op.create_index("ix_audits_auditor", "audits", ["auditor"])
    op.create_index("ix_audits_case_priority", "audits", ["case_priority"])
    op.create_index("ix_audits_customer_tier", "audits", ["customer_tier"])
    op.create_index("ix_audits_audit_type", "audits", ["audit_type"])
    op.create_index("ix_audits_total_score", "audits", ["total_score"])
    op.create_index("ix_audits_questionnaire_version_id", "audits", ["questionnaire_version_id"])

    op.create_table(
        "audit_responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("audit_id", sa.Integer(), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questionnaire_questions.id"), nullable=False),
        sa.Column("response_value", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("audit_id", "question_id", name="uq_audit_question"),
    )
    op.create_index("ix_audit_responses_audit_id", "audit_responses", ["audit_id"])
    op.create_index("ix_audit_responses_question_id", "audit_responses", ["question_id"])


def downgrade() -> None:
    op.drop_table("audit_responses")
    op.drop_table("audits")
    op.drop_table("questionnaire_options")
    op.drop_table("questionnaire_questions")
    op.drop_table("questionnaire_sections")
    op.drop_table("questionnaire_versions")
    op.drop_table("questionnaire_templates")
    op.drop_table("users")