from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin


class AdminUserEntity(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="super_admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
