from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True, unique=True)
    vk_id: Mapped[int] = mapped_column(nullable=True)
    ok_id: Mapped[int] = mapped_column(nullable=True)
    ya_id: Mapped[int] = mapped_column(nullable=True)
