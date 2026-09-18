from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.database_config import Base
from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import ConflictException, ValidationException
from app.model.admin_model import AdminUserCreateRequest, AdminUserUpdateRequest
from app.service.admin_user_service import AdminUserService


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_create_and_update_admin_user():
    db = _db_session()
    db.add(
        AdminUserEntity(
            email="seed@local",
            password_hash="hash",
            role="super_admin",
            is_active=True,
        )
    )
    db.commit()

    service = AdminUserService()
    created = service.create_user(
        db,
        AdminUserCreateRequest(email="analyst@example.com", password="password123", role="analyst"),
    ).data
    assert created is not None
    assert created.role == "analyst"

    updated = service.update_user(
        db,
        created.id,
        AdminUserUpdateRequest(role="config_editor", is_active=False),
    ).data
    assert updated is not None
    assert updated.role == "config_editor"
    assert updated.is_active is False


def test_create_admin_user_duplicate_email_rejected():
    db = _db_session()
    db.add(
        AdminUserEntity(
            email="dup@example.com",
            password_hash="hash",
            role="super_admin",
            is_active=True,
        )
    )
    db.commit()

    service = AdminUserService()
    try:
        service.create_user(
            db,
            AdminUserCreateRequest(email=" DUP@EXAMPLE.COM ", password="password123", role="analyst"),
        )
        assert False, "Expected ConflictException"
    except ConflictException:
        assert True


def test_last_active_super_admin_cannot_be_disabled_or_demoted():
    db = _db_session()
    db.add(
        AdminUserEntity(
            email="admin@local",
            password_hash="hash",
            role="super_admin",
            is_active=True,
        )
    )
    db.commit()

    service = AdminUserService()
    user = db.query(AdminUserEntity).filter_by(email="admin@local").one()
    for payload in (
        AdminUserUpdateRequest(role="super_admin", is_active=False),
        AdminUserUpdateRequest(role="analyst", is_active=True),
    ):
        try:
            service.update_user(db, user.id, payload)
            assert False, "Expected ValidationException"
        except ValidationException:
            assert True
