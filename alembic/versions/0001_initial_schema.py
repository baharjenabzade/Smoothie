"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("target_band", sa.Float(), server_default="7.0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("part", sa.SmallInteger(), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("cue_points", JSONType, nullable=True),
        sa.Column("is_ai_generated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"],
            name=op.f("fk_questions_created_by_users"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
    )
    op.create_index(op.f("ix_questions_part"), "questions", ["part"])
    op.create_index(op.f("ix_questions_topic"), "questions", ["topic"])

    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("part", sa.SmallInteger(), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_practice_sessions_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_practice_sessions")),
    )
    op.create_index(op.f("ix_practice_sessions_user_id"), "practice_sessions", ["user_id"])

    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["session_id"], ["practice_sessions.id"],
            name=op.f("fk_answers_session_id_practice_sessions"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_answers_user_id_users"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"],
            name=op.f("fk_answers_question_id_questions"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answers")),
    )
    op.create_index(op.f("ix_answers_session_id"), "answers", ["session_id"])
    op.create_index(op.f("ix_answers_user_id"), "answers", ["user_id"])

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fluency_score", sa.Float(), nullable=False),
        sa.Column("lexical_score", sa.Float(), nullable=False),
        sa.Column("grammar_score", sa.Float(), nullable=False),
        sa.Column("overall_band", sa.Float(), nullable=False),
        sa.Column("feedback", JSONType, nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["answer_id"], ["answers.id"],
            name=op.f("fk_evaluations_answer_id_answers"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_evaluations_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluations")),
        sa.UniqueConstraint("answer_id", name=op.f("uq_evaluations_answer_id")),
    )
    op.create_index(op.f("ix_evaluations_user_id"), "evaluations", ["user_id"])

    op.create_table(
        "grammar_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("original", sa.Text(), nullable=False),
        sa.Column("corrected", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["evaluation_id"], ["evaluations.id"],
            name=op.f("fk_grammar_issues_evaluation_id_evaluations"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_grammar_issues_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grammar_issues")),
    )
    op.create_index(op.f("ix_grammar_issues_evaluation_id"), "grammar_issues", ["evaluation_id"])
    op.create_index(op.f("ix_grammar_issues_user_id"), "grammar_issues", ["user_id"])
    op.create_index(op.f("ix_grammar_issues_category"), "grammar_issues", ["category"])

    op.create_table(
        "vocabulary_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), nullable=True),
        sa.Column("term", sa.String(length=200), nullable=False),
        sa.Column("term_key", sa.String(length=200), nullable=False),
        sa.Column("item_type", sa.String(length=30), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("topic", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=20), server_default="answer", nullable=False),
        sa.Column("times_seen", sa.Integer(), server_default="1", nullable=False),
        _created_at(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_vocabulary_items_user_id_users"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_id"], ["evaluations.id"],
            name=op.f("fk_vocabulary_items_evaluation_id_evaluations"), ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vocabulary_items")),
        sa.UniqueConstraint("user_id", "term_key", name="uq_vocabulary_items_user_id_term_key"),
    )
    op.create_index(op.f("ix_vocabulary_items_user_id"), "vocabulary_items", ["user_id"])
    op.create_index(op.f("ix_vocabulary_items_topic"), "vocabulary_items", ["topic"])


def downgrade() -> None:
    op.drop_table("vocabulary_items")
    op.drop_table("grammar_issues")
    op.drop_table("evaluations")
    op.drop_table("answers")
    op.drop_table("practice_sessions")
    op.drop_table("questions")
    op.drop_table("users")
