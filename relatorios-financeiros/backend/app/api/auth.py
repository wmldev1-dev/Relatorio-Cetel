"""Rotas de autenticacao."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, require_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse, UserResponse
from app.schemas.rbac import AuthPermissionsResponse
from app.services.auth_service import AuthService
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    """Autentica usuario e retorna access token."""
    authenticated = AuthService().authenticate(credentials.email, credentials.password)
    if authenticated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )
    access_token, user = authenticated
    return TokenResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Retorna usuario autenticado."""
    return UserResponse.model_validate(current_user)


@router.get("/permissions", response_model=AuthPermissionsResponse)
def permissions(current_user: User = Depends(require_active_user)) -> dict[str, object]:
    """Retorna papeis e permissoes do usuario autenticado."""
    return RBACService().get_permissions_payload(current_user.id)


@router.post("/logout", response_model=LogoutResponse)
def logout() -> LogoutResponse:
    """Confirma logout; o token e removido no frontend."""
    return LogoutResponse(success=True, message="Logout realizado com sucesso.")
