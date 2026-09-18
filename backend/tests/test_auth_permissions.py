import pytest

from app.config.auth_config import require_permission
from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import ForbiddenException


def _user(role: str) -> AdminUserEntity:
    return AdminUserEntity(email=f"{role}@local", password_hash="x", role=role, is_active=True)


def test_super_admin_has_all_permissions():
    guard = require_permission("rules:write")
    user = _user("super_admin")
    assert guard(user).role == "super_admin"
    assert require_permission("assessment_data:reset")(user).role == "super_admin"


def test_analyst_cannot_write_rules_or_manage_users():
    guard = require_permission("rules:write")
    user = _user("analyst")
    with pytest.raises(ForbiddenException):
        guard(user)

    with pytest.raises(ForbiddenException):
        require_permission("admin_users:read")(user)

    with pytest.raises(ForbiddenException):
        require_permission("assessment_data:reset")(user)


def test_analyst_allowed_research_read():
    guard = require_permission("research:read")
    user = _user("analyst")
    assert guard(user).role == "analyst"


def test_config_editor_can_manage_configuration_but_not_assessments():
    user = _user("config_editor")
    assert require_permission("rules:write")(user).role == "config_editor"
    assert require_permission("questionnaire:activate")(user).role == "config_editor"
    with pytest.raises(ForbiddenException):
        require_permission("assessments:read")(user)


def test_unknown_role_is_denied():
    with pytest.raises(ForbiddenException):
        require_permission("analytics:read")(_user("unknown"))
