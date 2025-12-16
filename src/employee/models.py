from typing import List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Position(Base):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    salary: Mapped[float] = mapped_column(nullable=False)

    employees: Mapped[List["Employee"]] = relationship(back_populates="position")


class Employee(Base):
    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    patronymic: Mapped[str] = mapped_column(nullable=True)

    position_id: Mapped[UUID] = mapped_column(
        ForeignKey("positions.id"),
        nullable=True,
    )
    position: Mapped[Optional["Position"]] = relationship(back_populates="properties")
