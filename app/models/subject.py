from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_subjects_user_id_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    owner: Mapped["User"] = relationship(back_populates="subjects")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="subject",
        passive_deletes=True,
    )
