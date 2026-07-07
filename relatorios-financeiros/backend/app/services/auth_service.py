"""Servico de autenticacao e provisionamento de usuarios."""

from __future__ import annotations

import logging

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import create_access_token, hash_password, verify_password
from app.core.settings import settings
from app.database.database import Database
from app.models.user import User
from app.services.rbac_service import RBACService

logger = logging.getLogger(__name__)


class AuthService:
    """Opera credenciais e usuarios autenticaveis."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def authenticate(self, email: str, password: str) -> tuple[str, User] | None:
        """Autentica credenciais e retorna token com usuario."""
        self.database.init_models()
        self.database.ensure_user_management_columns()
        with self.database.get_session() as session:
            user = self.get_user_by_email(session, email)
            now = datetime.utcnow()
            if user is None:
                return None
            if user.locked_until and user.locked_until > now:
                return None
            if not user.is_active or not verify_password(password, user.password_hash):
                self._register_failed_login(session, user, now)
                return None
            user.failed_login_attempts = 0
            user.first_failed_login_at = None
            user.locked_until = None
            user.last_login_at = now
            session.commit()
            token = create_access_token(str(user.id))
            return token, user

    def get_user_by_id(self, user_id: int) -> User | None:
        """Busca usuario por ID."""
        self.database.init_models()
        self.database.ensure_user_management_columns()
        with self.database.get_session() as session:
            return session.get(User, user_id)

    def get_user_by_email(self, session: Session, email: str) -> User | None:
        """Busca usuario por email normalizado."""
        normalized_email = email.strip().lower()
        statement = select(User).where(User.email == normalized_email)
        return session.execute(statement).scalar_one_or_none()

    def seed_initial_admin(self) -> tuple[bool, str]:
        """Cria usuario administrador inicial quando configurado e inexistente."""
        self.database.init_models()
        self.database.ensure_user_management_columns()
        if not settings.admin_password:
            return False, "ADMIN_PASSWORD vazio; admin inicial não criado."

        with self.database.get_session() as session:
            existing = session.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.email == settings.admin_email.strip().lower()),
            ).scalar_one_or_none()
            if existing is not None:
                RBACService(self.database).assign_admin_role(existing, session)
                session.commit()
                return False, "Admin inicial já existe."

            admin = User(
                name=settings.admin_name,
                email=settings.admin_email.strip().lower(),
                password_hash=hash_password(settings.admin_password),
                is_active=True,
                is_admin=True,
            )
            session.add(admin)
            session.flush()
            admin = session.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == admin.id),
            ).scalar_one()
            RBACService(self.database).assign_admin_role(admin, session)
            session.commit()
            logger.info("Usuario admin inicial criado: %s", admin.email)
            return True, "Admin inicial criado."

    def _register_failed_login(self, session: Session, user: User, now: datetime) -> None:
        """Registra tentativa invalida e aplica bloqueio temporario."""
        window_start = now - timedelta(minutes=15)
        if not user.first_failed_login_at or user.first_failed_login_at < window_start:
            user.first_failed_login_at = now
            user.failed_login_attempts = 1
        else:
            user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
        session.commit()
