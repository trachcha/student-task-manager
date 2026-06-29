"""add subjects and task subject

Revision ID: fae1e7ffb9e3
Revises: 911f2b0fa613
Create Date: 2026-06-30 00:01:37.469158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fae1e7ffb9e3'
down_revision: Union[str, Sequence[str], None] = '911f2b0fa613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_subjects_user_id_name"),
    )
    op.create_index("ix_subjects_user_id", "subjects", ["user_id"])

    op.add_column("tasks", sa.Column("subject_id", sa.Integer(), nullable=True))
    op.create_index("ix_tasks_subject_id", "tasks", ["subject_id"])
    op.create_foreign_key(
        "fk_tasks_subject_id_subjects",
        "tasks",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_tasks_subject_id_subjects", "tasks", type_="foreignkey")
    op.drop_index("ix_tasks_subject_id", table_name="tasks")
    op.drop_column("tasks", "subject_id")
    op.drop_index("ix_subjects_user_id", table_name="subjects")
    op.drop_table("subjects")
