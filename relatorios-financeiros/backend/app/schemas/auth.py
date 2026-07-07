"""Schemas de autenticacao."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import APIModel


class LoginRequest(BaseModel):
    """Credenciais de login."""

    email: str
    password: str


class UserResponse(APIModel):
    """Usuario retornado pela API sem dados sensiveis."""

    id: int
    name: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class TokenResponse(BaseModel):
    """Resposta com access token JWT."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    """Resposta simples de logout."""

    success: bool
    message: str
