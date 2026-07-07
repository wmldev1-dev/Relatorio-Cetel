"""Rotas administrativas de usuarios."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserMessageResponse,
    UserPasswordUpdate,
    UserUpdate,
)
from app.services.user_service import UserService, UserServiceError

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get(
    "",
    response_model=UserListResponse,
    dependencies=[Depends(require_permission("usuarios.view"))],
)
def list_users(
    nome: str | None = None,
    email: str | None = None,
    ativo: bool | None = None,
    papel: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    order_by: str = Query(default="created_at", pattern="^(nome|email|created_at)$"),
) -> dict[str, object]:
    """Lista usuarios administrativos."""
    return UserService().list_users(
        nome=nome,
        email=email,
        ativo=ativo,
        papel=papel,
        page=page,
        page_size=page_size,
        order_by=order_by,
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_permission("usuarios.view"))],
)
def get_user(user_id: int) -> dict[str, object]:
    """Busca usuario por ID."""
    try:
        return UserService().get_user(user_id)
    except UserServiceError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "",
    dependencies=[Depends(require_permission("usuarios.create"))],
)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission("usuarios.create")),
) -> dict[str, object]:
    """Cria usuario."""
    try:
        return UserService().create_user(payload, current_user)
    except UserServiceError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.put(
    "/{user_id}",
    dependencies=[Depends(require_permission("usuarios.update"))],
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_permission("usuarios.update")),
) -> dict[str, object]:
    """Atualiza usuario."""
    try:
        return UserService().update_user(user_id, payload, current_user)
    except UserServiceError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.patch(
    "/{user_id}/password",
    dependencies=[Depends(require_permission("usuarios.update"))],
)
def update_user_password(
    user_id: int,
    payload: UserPasswordUpdate,
    current_user: User = Depends(require_permission("usuarios.update")),
) -> dict[str, object]:
    """Altera senha de usuario."""
    try:
        return UserService().update_password(user_id, payload.senha, current_user)
    except UserServiceError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.delete(
    "/{user_id}",
    response_model=UserMessageResponse,
    dependencies=[Depends(require_permission("usuarios.delete"))],
)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("usuarios.delete")),
) -> dict[str, bool | str]:
    """Exclui logicamente usuario."""
    try:
        return UserService().deactivate_user(user_id, current_user)
    except UserServiceError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
