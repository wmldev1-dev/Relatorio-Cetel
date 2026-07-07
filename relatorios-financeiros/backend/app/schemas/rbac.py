"""Schemas de papeis e permissoes."""

from __future__ import annotations

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    """Permissao retornada ao frontend."""

    module: str
    action: str
    code: str
    description: str | None = None


class RoleResponse(BaseModel):
    """Papel retornado ao frontend."""

    name: str
    description: str | None = None
    is_system: bool


class AuthPermissionsResponse(BaseModel):
    """Papeis e permissoes do usuario autenticado."""

    roles: list[RoleResponse]
    permissions: list[PermissionResponse]
