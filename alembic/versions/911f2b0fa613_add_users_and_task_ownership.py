"""add users and task ownership

Revision ID: 911f2b0fa613
Revises: 0a83f21f05a3
Create Date: 2026-06-29 23:34:15.089494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '911f2b0fa613'
down_revision: Union[str, Sequence[str], None] = '0a83f21f05a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Existing tasks have no owner; this column is NOT NULL with no default, so
    # apply against a database whose `tasks` table is empty (dev data is
    # disposable - recreate the DB or clear `tasks` before upgrading).
    op.add_column("tasks", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_foreign_key(
        "fk_tasks_user_id_users",
        "tasks",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_tasks_user_id_users", "tasks", type_="foreignkey")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_column("tasks", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
