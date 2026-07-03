"""add task position

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-07-03 00:00:00.000000

"""
from collections import defaultdict
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )

    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, user_id, completed FROM tasks ORDER BY user_id, completed, id")
    ).fetchall()

    groups: dict[tuple[int, bool], list[int]] = defaultdict(list)
    for row in rows:
        groups[(row.user_id, row.completed)].append(row.id)

    for ids in groups.values():
        for position, task_id in enumerate(ids):
            conn.execute(
                text("UPDATE tasks SET position = :position WHERE id = :id"),
                {"position": position, "id": task_id},
            )

    op.alter_column("tasks", "position", server_default=None)


def downgrade() -> None:
    op.drop_column("tasks", "position")
