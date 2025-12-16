from typing import List
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ItemCategory(Base):
    __tablename__ = "item_catogories"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    item: Mapped[List["MenuItem"]] = relationship(back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)

    category_id: Mapped[UUID] = mapped_column(ForeignKey("item_catogories.id"))
    category: Mapped["ItemCategory"] = relationship(back_populates="item")
