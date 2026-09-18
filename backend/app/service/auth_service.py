from datetime import datetime, timedelta, timezone
from http import HTTPStatus
import logging

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.config import settings
from app.entity.admin_user_entity import AdminUserEntity
from app.exceptions.domain_exception import ServiceException, UnauthorizedException
from app.model.admin_model import AdminLoginData, AdminLoginRequest
from app.repository.admin_repository import AdminRepository
from app.util.response import GenericResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, subject: str) -> str:
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
        payload = {"sub": subject, "exp": expires}
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def login(self, db: Session, payload: AdminLoginRequest) -> GenericResponse[AdminLoginData]:
        email = payload.email.strip().lower()
        logger.info("AuthService.login started email=%s", email)
        try:
            user = AdminRepository(db).get_by_email(email)
            if not user or not user.is_active or not self.verify_password(payload.password, user.password_hash):
                logger.warning("AuthService.login invalid credentials email=%s", email)
                raise UnauthorizedException()
            logger.info("AuthService.login successful email=%s", payload.email)
            return GenericResponse.success_response(
                "Login successful.",
                data=AdminLoginData(access_token=self.create_access_token(user.email)),
                status_code=HTTPStatus.OK,
            )
        except UnauthorizedException:
            raise
        except Exception:
            logger.exception("AuthService.login failed unexpectedly.")
            raise ServiceException() from None

    def seed_default_admin(self, db: Session) -> None:
        if AdminRepository(db).get_by_email("admin@methodalign.local"):
            return
        db.add(
            AdminUserEntity(
                email="admin@methodalign.local",
                password_hash=self.hash_password("admin123"),
                role="super_admin",
                is_active=True,
            )
        )
        db.commit()
