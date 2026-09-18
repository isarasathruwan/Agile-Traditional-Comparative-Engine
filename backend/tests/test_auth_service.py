from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import UnauthorizedException
from app.model.admin_model import AdminLoginRequest
from app.service.auth_service import AuthService


def test_inactive_admin_cannot_log_in_even_with_valid_password():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    auth_service = AuthService()
    db.add(
        AdminUserEntity(
            email="inactive@local.test",
            password_hash=auth_service.hash_password("password123"),
            role="analyst",
            is_active=False,
        )
    )
    db.commit()

    try:
        auth_service.login(db, AdminLoginRequest(email=" INACTIVE@LOCAL.TEST ", password="password123"))
        assert False, "Expected UnauthorizedException"
    except UnauthorizedException:
        assert True
