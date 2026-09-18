from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entity.admin_user_entity import AdminUserEntity


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> AdminUserEntity | None:
        return self.db.scalar(select(AdminUserEntity).where(AdminUserEntity.email == email))

    def list_users(self) -> list[AdminUserEntity]:
        return list(self.db.scalars(select(AdminUserEntity).order_by(AdminUserEntity.created_at.desc())))

    def create_user(self, user: AdminUserEntity) -> AdminUserEntity:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count_active_super_admins(self) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(AdminUserEntity)
                .where(
                    AdminUserEntity.role == "super_admin",
                    AdminUserEntity.is_active.is_(True),
                )
            )
            or 0
        )

    def get_by_id(self, user_id: int) -> AdminUserEntity | None:
        return self.db.get(AdminUserEntity, user_id)

    def save(self, user: AdminUserEntity) -> AdminUserEntity:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
