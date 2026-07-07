"""Servico de papeis e permissoes."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.database import Database
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

MODULES = (
    "dashboard",
    "comparativo",
    "fornecedores",
    "servicos",
    "categorias",
    "dados_financeiros",
    "importacao",
    "diagnostico",
    "usuarios",
    "configuracoes",
)
ACTIONS = ("view", "create", "update", "delete", "export")

ROLE_DEFINITIONS: dict[str, dict[str, object]] = {
    "ADMIN": {
        "description": "Acesso administrativo completo.",
        "permissions": "all",
    },
    "FINANCEIRO": {
        "description": "Operação financeira sem gerenciamento de usuários.",
        "permissions": {
            "dashboard.*",
            "comparativo.*",
            "fornecedores.*",
            "servicos.*",
            "categorias.*",
            "dados_financeiros.*",
            "importacao.*",
            "diagnostico.*",
        },
    },
    "CONSULTA": {
        "description": "Consulta gerencial sem importação, diagnóstico ou exportação.",
        "permissions": {
            "dashboard.view",
            "comparativo.view",
            "fornecedores.view",
            "servicos.view",
            "categorias.view",
            "dados_financeiros.view",
        },
    },
}


@dataclass(frozen=True)
class UserAccess:
    """Permissoes cacheadas do usuario autenticado."""

    roles: tuple[str, ...]
    permissions: frozenset[str]


class RBACService:
    """Gerencia seed e consulta de RBAC."""

    _cache: dict[int, tuple[float, UserAccess]] = {}
    _cache_ttl_seconds = 300

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def seed_defaults(self) -> None:
        """Cria permissoes, papeis padrao e suas associacoes."""
        self.database.init_models()
        with self.database.get_session() as session:
            permissions = self._ensure_permissions(session)
            roles = self._ensure_roles(session)
            for role_name, definition in ROLE_DEFINITIONS.items():
                role = roles[role_name]
                role.permissions = [
                    permission for code, permission in permissions.items()
                    if self._role_has_permission(definition["permissions"], code)
                ]
            session.commit()
        self.clear_cache()

    def assign_admin_role(self, user: User, session: Session) -> None:
        """Garante que um usuario possua o papel ADMIN."""
        role = session.execute(select(Role).where(Role.name == "ADMIN")).scalar_one_or_none()
        if role is None:
            return
        if all(existing.name != "ADMIN" for existing in user.roles):
            user.roles.append(role)
            session.flush()
            self.clear_cache(user.id)

    def get_user_access(self, user_id: int) -> UserAccess:
        """Retorna papeis e permissoes do usuario com cache curto."""
        cached = self._cache.get(user_id)
        if cached and monotonic() - cached[0] <= self._cache_ttl_seconds:
            return cached[1]

        self.database.init_models()
        with self.database.get_session() as session:
            user = session.execute(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == user_id),
            ).scalar_one_or_none()
            if user is None:
                access = UserAccess(roles=(), permissions=frozenset())
            else:
                roles = tuple(sorted(role.name for role in user.roles))
                permissions = frozenset(
                    permission.code
                    for role in user.roles
                    for permission in role.permissions
                )
                access = UserAccess(roles=roles, permissions=permissions)

        self._cache[user_id] = (monotonic(), access)
        return access

    def get_permissions_payload(self, user_id: int) -> dict[str, object]:
        """Retorna payload de papeis e permissoes para /api/auth/permissions."""
        access = self.get_user_access(user_id)
        permission_items = [
            self._permission_payload(code)
            for code in sorted(access.permissions)
        ]
        return {
            "roles": [
                {
                    "name": role,
                    "description": str(ROLE_DEFINITIONS.get(role, {}).get("description") or ""),
                    "is_system": role in ROLE_DEFINITIONS,
                }
                for role in access.roles
            ],
            "permissions": permission_items,
        }

    def has_permission(self, user_id: int, permission: str) -> bool:
        """Verifica se usuario possui permissao especifica."""
        return permission in self.get_user_access(user_id).permissions

    def has_module(self, user_id: int, module: str) -> bool:
        """Verifica se usuario possui qualquer permissao de visualizacao no modulo."""
        return f"{module}.view" in self.get_user_access(user_id).permissions

    @classmethod
    def clear_cache(cls, user_id: int | None = None) -> None:
        """Limpa cache de permissoes."""
        if user_id is None:
            cls._cache.clear()
            return
        cls._cache.pop(user_id, None)

    def _ensure_permissions(self, session: Session) -> dict[str, Permission]:
        existing = {
            permission.code: permission
            for permission in session.execute(select(Permission)).scalars()
        }
        for module in MODULES:
            for action in ACTIONS:
                code = f"{module}.{action}"
                if code not in existing:
                    existing[code] = Permission(
                        module=module,
                        action=action,
                        description=f"Permite {action} em {module}.",
                    )
                    session.add(existing[code])
        session.flush()
        return existing

    def _ensure_roles(self, session: Session) -> dict[str, Role]:
        existing = {
            role.name: role
            for role in session.execute(
                select(Role).options(selectinload(Role.permissions)),
            ).scalars()
        }
        for role_name, definition in ROLE_DEFINITIONS.items():
            role = existing.get(role_name)
            if role is None:
                role = Role(
                    name=role_name,
                    description=str(definition["description"]),
                    is_system=True,
                )
                existing[role_name] = role
                session.add(role)
            else:
                role.description = str(definition["description"])
                role.is_system = True
        session.flush()
        return existing

    @staticmethod
    def _role_has_permission(definition: object, code: str) -> bool:
        if definition == "all":
            return True
        if not isinstance(definition, set):
            return False
        module, _action = code.split(".", 1)
        return code in definition or f"{module}.*" in definition

    @staticmethod
    def _permission_payload(code: str) -> dict[str, str]:
        module, action = code.split(".", 1)
        return {
            "module": module,
            "action": action,
            "code": code,
            "description": f"Permite {action} em {module}.",
        }
