"""Servico administrativo de usuarios."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.database.database import Database
from app.models.role import Role
from app.models.user import User
from app.models.user_audit import UserAuditLog
from app.schemas.user import UserCreate, UserUpdate
from app.services.rbac_service import RBACService

SYSTEM_ROLES = ("ADMIN", "FINANCEIRO", "CONSULTA")


class UserServiceError(ValueError):
    """Erro de negocio da gestao de usuarios."""


class UserService:
    """Casos de uso administrativos para usuarios."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_users(
        self,
        nome: str | None = None,
        email: str | None = None,
        ativo: bool | None = None,
        papel: str | None = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
    ) -> dict[str, Any]:
        """Lista usuarios com filtros, ordenacao e paginacao."""
        self.database.init_models()
        self.database.ensure_user_management_columns()
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        with self.database.get_session() as session:
            statement = select(User).options(selectinload(User.roles))
            count_statement = select(func.count(User.id))
            statement, count_statement = self._apply_filters(
                statement,
                count_statement,
                nome=nome,
                email=email,
                ativo=ativo,
                papel=papel,
            )
            sort_column = {
                "nome": User.name,
                "email": User.email,
                "created_at": User.created_at,
            }.get(order_by, User.created_at)
            statement = (
                statement.order_by(sort_column.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            total = int(session.execute(count_statement).scalar_one())
            users = session.execute(statement).scalars().unique().all()
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [self._serialize_user(user) for user in users],
            }

    def get_user(self, user_id: int) -> dict[str, Any]:
        """Busca usuario por ID."""
        with self._session() as session:
            user = self._get_user_or_raise(session, user_id)
            return self._serialize_user(user)

    def create_user(self, payload: UserCreate, actor: User) -> dict[str, Any]:
        """Cria usuario administrativo."""
        with self._session() as session:
            self._ensure_unique_email(session, payload.email)
            roles = self._get_roles(session, payload.papeis)
            user = User(
                name=payload.nome.strip(),
                email=payload.email,
                password_hash=hash_password(payload.senha),
                is_active=payload.ativo,
                is_admin=any(role.name == "ADMIN" for role in roles),
                created_by_id=actor.id,
                updated_by_id=actor.id,
            )
            user.roles = roles
            session.add(user)
            session.flush()
            self._audit(session, user.id, actor.id, "create", "Usuário criado.")
            session.commit()
            RBACService.clear_cache(user.id)
            return self.get_user(user.id)

    def update_user(self, user_id: int, payload: UserUpdate, actor: User) -> dict[str, Any]:
        """Atualiza dados e papeis de usuario."""
        with self._session() as session:
            user = self._get_user_or_raise(session, user_id)
            self._ensure_not_self_deactivation(user, actor, payload.ativo)
            roles = self._get_roles(session, payload.papeis)
            self._ensure_not_last_admin_change(session, user, roles, payload.ativo)
            self._ensure_unique_email(session, payload.email, user_id=user.id)
            user.name = payload.nome.strip()
            user.email = payload.email
            user.is_active = payload.ativo
            user.roles = roles
            user.is_admin = any(role.name == "ADMIN" for role in roles)
            user.updated_by_id = actor.id
            self._audit(session, user.id, actor.id, "update", "Usuário atualizado.")
            session.commit()
            RBACService.clear_cache(user.id)
            return self.get_user(user.id)

    def update_password(self, user_id: int, senha: str, actor: User) -> dict[str, Any]:
        """Atualiza senha de usuario."""
        with self._session() as session:
            user = self._get_user_or_raise(session, user_id)
            user.password_hash = hash_password(senha)
            user.failed_login_attempts = 0
            user.first_failed_login_at = None
            user.locked_until = None
            user.updated_by_id = actor.id
            self._audit(session, user.id, actor.id, "password", "Senha alterada.")
            session.commit()
            return self.get_user(user.id)

    def deactivate_user(self, user_id: int, actor: User) -> dict[str, bool | str]:
        """Exclui logicamente usuario."""
        with self._session() as session:
            user = self._get_user_or_raise(session, user_id)
            if user.id == actor.id:
                raise UserServiceError("Você não pode excluir ou desativar a si mesmo.")
            self._ensure_not_last_admin_change(session, user, list(user.roles), False)
            user.is_active = False
            user.updated_by_id = actor.id
            self._audit(session, user.id, actor.id, "delete", "Usuário desativado.")
            session.commit()
            RBACService.clear_cache(user.id)
            return {"success": True, "message": "Usuário desativado com sucesso."}

    def _session(self) -> Session:
        self.database.init_models()
        self.database.ensure_user_management_columns()
        return self.database.get_session()

    def _apply_filters(
        self,
        statement: Any,
        count_statement: Any,
        nome: str | None,
        email: str | None,
        ativo: bool | None,
        papel: str | None,
    ) -> tuple[Any, Any]:
        conditions = []
        if nome:
            conditions.append(User.name.ilike(f"%{nome.strip()}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email.strip().lower()}%"))
        if ativo is not None:
            conditions.append(User.is_active.is_(ativo))
        if papel:
            statement = statement.join(User.roles)
            count_statement = count_statement.select_from(User).join(User.roles)
            conditions.append(Role.name == papel.strip().upper())
        for condition in conditions:
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)
        return statement, count_statement

    def _get_user_or_raise(self, session: Session, user_id: int) -> User:
        user = session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id),
        ).scalar_one_or_none()
        if user is None:
            raise UserServiceError("Usuário não encontrado.")
        return user

    def _get_roles(self, session: Session, role_names: list[str]) -> list[Role]:
        normalized = {role.strip().upper() for role in role_names if role.strip()}
        invalid = normalized.difference(SYSTEM_ROLES)
        if invalid:
            raise UserServiceError(f"Papéis inválidos: {', '.join(sorted(invalid))}.")
        if not normalized:
            raise UserServiceError("Selecione pelo menos um papel.")
        roles = session.execute(select(Role).where(Role.name.in_(normalized))).scalars().all()
        found = {role.name for role in roles}
        missing = normalized.difference(found)
        if missing:
            raise UserServiceError(f"Papéis não encontrados: {', '.join(sorted(missing))}.")
        return list(roles)

    def _ensure_unique_email(
        self,
        session: Session,
        email: str,
        user_id: int | None = None,
    ) -> None:
        statement = select(User).where(User.email == email.strip().lower())
        if user_id is not None:
            statement = statement.where(User.id != user_id)
        if session.execute(statement).scalar_one_or_none() is not None:
            raise UserServiceError("Já existe um usuário com este email.")

    def _ensure_not_self_deactivation(self, user: User, actor: User, active: bool) -> None:
        if user.id == actor.id and not active:
            raise UserServiceError("Você não pode desativar a si mesmo.")

    def _ensure_not_last_admin_change(
        self,
        session: Session,
        user: User,
        new_roles: list[Role],
        active: bool,
    ) -> None:
        is_admin_now = any(role.name == "ADMIN" for role in user.roles) and user.is_active
        will_be_admin = any(role.name == "ADMIN" for role in new_roles) and active
        if is_admin_now and not will_be_admin and self._active_admin_count(session) <= 1:
            raise UserServiceError("Não é permitido remover ou desativar o último ADMIN.")

    def _active_admin_count(self, session: Session) -> int:
        return int(
            session.execute(
                select(func.count(User.id))
                .join(User.roles)
                .where(User.is_active.is_(True), Role.name == "ADMIN"),
            ).scalar_one(),
        )

    def _audit(
        self,
        session: Session,
        user_id: int,
        actor_user_id: int | None,
        action: str,
        description: str,
    ) -> None:
        session.add(
            UserAuditLog(
                user_id=user_id,
                actor_user_id=actor_user_id,
                action=action,
                description=description,
            ),
        )

    def _serialize_user(self, user: User) -> dict[str, Any]:
        roles = sorted(user.roles, key=lambda role: role.name)
        return {
            "id": user.id,
            "nome": user.name,
            "email": user.email,
            "ativo": user.is_active,
            "is_admin": user.is_admin,
            "papeis": [
                {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "is_system": role.is_system,
                }
                for role in roles
            ],
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login_at": user.last_login_at,
            "created_by_id": user.created_by_id,
            "updated_by_id": user.updated_by_id,
        }
