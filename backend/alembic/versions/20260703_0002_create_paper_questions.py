"""create paper_questions table

Revision ID: 20260703_0002
Revises: 20260606_0001
Create Date: 2026-07-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260703_0002"
down_revision: Union[str, None] = "20260606_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paper_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paper_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_paper_questions_id"), "paper_questions", ["id"], unique=False)
    op.create_index(op.f("ix_paper_questions_paper_id"), "paper_questions", ["paper_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_paper_questions_paper_id"), table_name="paper_questions")
    op.drop_index(op.f("ix_paper_questions_id"), table_name="paper_questions")
    op.drop_table("paper_questions")
