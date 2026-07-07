"""Seeds seguros executados no startup da aplicacao."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.core.settings import settings
from app.database.database import Database
from app.models.user import User
from app.services.rbac_service import RBACService

logger = logging.getLogger(__name__)


def run_startup_seeds() -> None:
    """Executa seeds obrigatorios em ordem segura."""
    database = Database()
    RBACService(database).seed_defaults()
    ensure_admin_user(database)


def ensure_admin_user(database: Database | None = None) -> None:
    """Garante usuario administrador inicial ativo e com papel ADMIN."""
    database = database or Database()
    admin_email = settings.admin_email.strip().lower()
    admin_password = settings.admin_password

    if not admin_email or not admin_password:
        logger.warning(
            "ADMIN_EMAIL ou ADMIN_PASSWORD vazio; usuario ADMIN inicial nao criado.",
        )
        return

    database.init_models()
    database.ensure_user_management_columns()
    rbac_service = RBACService(database)

    with database.get_session() as session:
        admin = session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == admin_email),
        ).scalar_one_or_none()

        if admin is None:
            admin = User(
                name=settings.admin_name.strip() or "Administrador",
                email=admin_email,
                password_hash=get_password_hash(admin_password),
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
            logger.info("Admin inicial criado: %s", admin.email)
        else:
            logger.info("Admin inicial ja existia: %s", admin.email)
            if not admin.is_active:
                admin.is_active = True
                logger.info("Admin inicial ativado: %s", admin.email)
            if not admin.is_admin:
                admin.is_admin = True
                logger.info("Admin inicial marcado como administrador: %s", admin.email)
            if settings.admin_reset_password_on_startup:
                admin.password_hash = get_password_hash(admin_password)
                logger.warning(
                    "Senha do admin inicial redefinida no startup: %s",
                    admin.email,
                )

        had_admin_role = any(role.name == "ADMIN" for role in admin.roles)
        rbac_service.assign_admin_role(admin, session)
        if not had_admin_role:
            logger.info("Admin inicial recebeu papel ADMIN: %s", admin.email)

        session.commit()
