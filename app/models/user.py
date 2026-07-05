from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.task import Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    unsorted_label: Mapped[str] = mapped_column(default="Unsorted")
    unsorted_position: Mapped[int] = mapped_column(default=0)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
