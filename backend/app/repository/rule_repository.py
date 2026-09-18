from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entity.rule_config_entity import RuleConfigVersionEntity


class RuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> RuleConfigVersionEntity | None:
        return self.db.scalar(
            select(RuleConfigVersionEntity).where(RuleConfigVersionEntity.is_active.is_(True))
        )

    def get_latest_version(self) -> int:
        return self.db.scalar(select(RuleConfigVersionEntity.version).order_by(RuleConfigVersionEntity.version.desc())) or 0

    def get_by_version(self, version: int) -> RuleConfigVersionEntity | None:
        return self.db.scalar(
            select(RuleConfigVersionEntity).where(RuleConfigVersionEntity.version == version)
        )

    def list_versions(self) -> list[RuleConfigVersionEntity]:
        return list(
            self.db.scalars(
                select(RuleConfigVersionEntity).order_by(RuleConfigVersionEntity.version.desc())
            )
        )

    def deactivate(self, row: RuleConfigVersionEntity) -> None:
        row.is_active = False

    def create(self, row: RuleConfigVersionEntity) -> RuleConfigVersionEntity:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def commit(self) -> None:
        self.db.commit()
