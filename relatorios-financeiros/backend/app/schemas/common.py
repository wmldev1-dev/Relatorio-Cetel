"""Schemas compartilhados da API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Resposta padrao para operacoes de comando."""

    success: bool
    message: str


class HealthResponse(BaseModel):
    """Resposta de saude da API."""

    status: str
    database: str


class APIModel(BaseModel):
    """Base Pydantic com serializacao ORM habilitada."""

    model_config = ConfigDict(from_attributes=True)
