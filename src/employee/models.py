from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Position(Base):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    salary: Mapped[float] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    department: Mapped[str] = mapped_column(nullable=True)

    employees: Mapped[List["Employee"]] = relationship(back_populates="position")


class Employee(Base):
    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    patronymic: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True, unique=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    hire_date: Mapped[date] = mapped_column(nullable=True)
    birth_date: Mapped[date] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    position_id: Mapped[UUID] = mapped_column(
        ForeignKey("positions.id"),
        nullable=True,
    )
    position: Mapped[Optional["Position"]] = relationship(back_populates="employees")


class Shift(Base):
    __tablename__ = "shifts"

    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"))
    employee: Mapped["Employee"] = relationship()

    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(nullable=True)
    is_closed: Mapped[bool] = mapped_column(default=False, nullable=False)
    break_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
