from typing import List
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ItemCategory(Base):
    __tablename__ = "item_catogories"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    color: Mapped[str] = mapped_column(nullable=True)

    item: Mapped[List["MenuItem"]] = relationship(back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    quantity: Mapped[int] = mapped_column(default=0)
    price: Mapped[float] = mapped_column(default=0.0, nullable=False)
    sku: Mapped[str] = mapped_column(nullable=True, unique=True)
    is_available: Mapped[bool] = mapped_column(default=True, nullable=False)

    category_id: Mapped[UUID] = mapped_column(ForeignKey("item_catogories.id"))
    category: Mapped["ItemCategory"] = relationship(back_populates="item")
