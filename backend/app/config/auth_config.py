from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config.database_config import get_db
from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import ForbiddenException, UnauthorizedException
from app.repository.admin_repository import AdminRepository


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "rules:read",
        "rules:write",
        "rules:activate",
        "analytics:read",
        "research:read",
        "assessments:read",
        "assessments:write",
        "assessment_data:reset",
        "assessments:export",
        "questionnaire:read",
        "questionnaire:write",
        "questionnaire:activate",
        "admin_users:read",
        "admin_users:write",
    },
    "analyst": {
        "analytics:read",
        "research:read",
        "assessments:read",
        "assessments:export",
    },
    "config_editor": {
        "rules:read",
        "rules:write",
        "rules:activate",
        "questionnaire:read",
        "questionnaire:write",
        "questionnaire:activate",
        "analytics:read",
    },
}


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> AdminUserEntity:
    email = getattr(request.state, "user_subject", None)
    if not email:
        raise UnauthorizedException("Not authenticated.")
    user = AdminRepository(db).get_by_email(email)
    if not user or not user.is_active:
        raise UnauthorizedException("Invalid user.")
    return user


def require_permission(permission: str):
    def _guard(user: AdminUserEntity = Depends(get_current_admin)) -> AdminUserEntity:
        permissions = ROLE_PERMISSIONS.get(user.role, set())
        if permission not in permissions:
            raise ForbiddenException()
        return user

    return _guard
