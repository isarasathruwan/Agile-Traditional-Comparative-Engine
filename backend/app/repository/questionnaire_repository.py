from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entity.questionnaire_entity import QuestionnaireVersionEntity


class QuestionnaireRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> QuestionnaireVersionEntity | None:
        return self.db.scalar(
            select(QuestionnaireVersionEntity).where(QuestionnaireVersionEntity.is_active.is_(True))
        )

    def get_latest_version(self) -> int:
        return (
            self.db.scalar(
                select(QuestionnaireVersionEntity.version).order_by(QuestionnaireVersionEntity.version.desc())
            )
            or 0
        )

    def get_by_version(self, version: int) -> QuestionnaireVersionEntity | None:
        return self.db.scalar(
            select(QuestionnaireVersionEntity).where(QuestionnaireVersionEntity.version == version)
        )

    def list_versions(self) -> list[QuestionnaireVersionEntity]:
        return list(
            self.db.scalars(
                select(QuestionnaireVersionEntity).order_by(QuestionnaireVersionEntity.version.desc())
            )
        )

    def deactivate(self, row: QuestionnaireVersionEntity) -> None:
        row.is_active = False

    def create(self, row: QuestionnaireVersionEntity) -> QuestionnaireVersionEntity:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def commit(self) -> None:
        self.db.commit()
