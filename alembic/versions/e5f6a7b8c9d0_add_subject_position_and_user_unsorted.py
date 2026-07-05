"""add subject position and user unsorted prefs

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-03 12:00:00.000000

"""
from collections import defaultdict
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subjects",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column(
            "unsorted_label",
            sa.String(),
            nullable=False,
            server_default="Unsorted",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "unsorted_position",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, user_id FROM subjects ORDER BY user_id, id")
    ).fetchall()

    groups: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        groups[row.user_id].append(row.id)

    for ids in groups.values():
        for position, subject_id in enumerate(ids):
            conn.execute(
                text("UPDATE subjects SET position = :position WHERE id = :id"),
                {"position": position, "id": subject_id},
            )

    op.alter_column("subjects", "position", server_default=None)
    op.alter_column("users", "unsorted_label", server_default=None)
    op.alter_column("users", "unsorted_position", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "unsorted_position")
    op.drop_column("users", "unsorted_label")
    op.drop_column("subjects", "position")
