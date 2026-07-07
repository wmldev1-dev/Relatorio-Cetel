"""Dependencias de autorizacao por permissao."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.dependencies import require_active_user
from app.models.user import User
from app.services.rbac_service import RBACService


def current_permissions(current_user: User = Depends(require_active_user)) -> set[str]:
    """Retorna permissoes do usuario autenticado."""
    access = RBACService().get_user_access(current_user.id)
    return set(access.permissions)


def require_permission(permission: str) -> Callable[[User], User]:
    """Cria dependencia que exige uma permissao especifica."""

    def dependency(current_user: User = Depends(require_active_user)) -> User:
        if not RBACService().has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Permissão necessária: {permission}.",
            )
        return current_user

    return dependency


def require_module(module: str) -> Callable[[User], User]:
    """Cria dependencia que exige visualizacao em um modulo."""

    def dependency(current_user: User = Depends(require_active_user)) -> User:
        if not RBACService().has_module(current_user.id, module):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado ao módulo {module}.",
            )
        return current_user

    return dependency


def permission_required(permission: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Decorator reutilizavel para marcar endpoints com permissao."""

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        setattr(func, "required_permission", permission)
        return func

    return decorator
