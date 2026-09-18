import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import ConflictException, NotFoundException, ServiceException, ValidationException
from app.model.admin_model import AdminUserCreateRequest, AdminUserData, AdminUserUpdateRequest
from app.repository.admin_repository import AdminRepository
from app.service.auth_service import AuthService
from app.util.response import GenericResponse

logger = logging.getLogger(__name__)


class AdminUserService:
    ALLOWED_ROLES = {"super_admin", "analyst", "config_editor"}

    @staticmethod
    def _serialize(user: AdminUserEntity) -> AdminUserData:
        return AdminUserData(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )

    def list_users(self, db: Session) -> GenericResponse[list[AdminUserData]]:
        logger.info("AdminUserService.list_users started.")
        try:
            users = AdminRepository(db).list_users()
            return GenericResponse.success_response(
                "Admin users fetched.",
                data=[self._serialize(user) for user in users],
            )
        except Exception:
            logger.exception("AdminUserService.list_users failed unexpectedly.")
            raise ServiceException("Unable to fetch admin users.") from None

    def create_user(self, db: Session, payload: AdminUserCreateRequest) -> GenericResponse[AdminUserData]:
        logger.info("AdminUserService.create_user started email=%s", payload.email)
        try:
            role = payload.role.strip().lower()
            email = str(payload.email).strip().lower()
            if role not in self.ALLOWED_ROLES:
                raise ValidationException("Invalid role.")
            repository = AdminRepository(db)
            if repository.get_by_email(email):
                raise ConflictException("An admin user with this email already exists.")
            user = repository.create_user(
                AdminUserEntity(
                    email=email,
                    password_hash=AuthService.hash_password(payload.password),
                    role=role,
                    is_active=True,
                )
            )
            return GenericResponse.success_response("Admin user created.", data=self._serialize(user))
        except IntegrityError:
            db.rollback()
            raise ConflictException("An admin user with this email already exists.") from None
        except (ConflictException, ValidationException):
            raise
        except Exception:
            logger.exception("AdminUserService.create_user failed unexpectedly.")
            raise ServiceException("Unable to create admin user.") from None

    def update_user(
        self, db: Session, user_id: int, payload: AdminUserUpdateRequest
    ) -> GenericResponse[AdminUserData]:
        logger.info("AdminUserService.update_user started user_id=%s", user_id)
        try:
            role = payload.role.strip().lower()
            if role not in self.ALLOWED_ROLES:
                raise ValidationException("Invalid role.")
            repository = AdminRepository(db)
            user = repository.get_by_id(user_id)
            if not user:
                raise NotFoundException("Admin user not found.")
            removes_last_super_admin = (
                user.role == "super_admin"
                and user.is_active
                and (role != "super_admin" or not payload.is_active)
                and repository.count_active_super_admins() <= 1
            )
            if removes_last_super_admin:
                raise ValidationException("At least one active super admin must remain.")
            user.role = role
            user.is_active = payload.is_active
            updated = repository.save(user)
            return GenericResponse.success_response("Admin user updated.", data=self._serialize(updated))
        except (ValidationException, NotFoundException):
            raise
        except Exception:
            logger.exception("AdminUserService.update_user failed unexpectedly.")
            raise ServiceException("Unable to update admin user.") from None
