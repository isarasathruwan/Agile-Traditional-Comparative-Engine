from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database_config import Base
from app.entity.base_mixin import TimestampMixin


class RuleConfigVersionEntity(Base, TimestampMixin):
    __tablename__ = "rule_config_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_by: Mapped[str] = mapped_column(String(255), default="system")
    change_note: Mapped[str] = mapped_column(String(500), default="")
