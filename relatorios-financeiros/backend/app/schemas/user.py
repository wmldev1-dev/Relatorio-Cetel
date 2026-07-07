"""Schemas da gestao administrativa de usuarios."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserRoleItem(BaseModel):
    """Papel associado a um usuario."""

    id: int
    name: str
    description: str | None = None
    is_system: bool


class UserListItem(BaseModel):
    """Usuario listado no painel administrativo."""

    id: int
    nome: str
    email: str
    ativo: bool
    is_admin: bool
    papeis: list[UserRoleItem]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None


class UserListResponse(BaseModel):
    """Resposta paginada de usuarios."""

    total: int
    page: int
    page_size: int
    items: list[UserListItem]


class UserCreate(BaseModel):
    """Payload de criacao de usuario."""

    nome: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    senha: str = Field(min_length=8, max_length=128)
    ativo: bool = True
    papeis: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Valida email simples sem bloquear dominios locais."""
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Email inválido.")
        return normalized


class UserUpdate(BaseModel):
    """Payload de edicao de usuario."""

    nome: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    ativo: bool = True
    papeis: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Valida email simples sem bloquear dominios locais."""
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Email inválido.")
        return normalized


class UserPasswordUpdate(BaseModel):
    """Payload de alteracao de senha."""

    senha: str = Field(min_length=8, max_length=128)


class UserMessageResponse(BaseModel):
    """Resposta de comando de usuario."""

    success: bool
    message: str
