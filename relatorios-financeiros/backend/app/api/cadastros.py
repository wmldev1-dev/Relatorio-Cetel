"""Rotas de listas derivadas dos lancamentos."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.financial_entry_service import FinancialEntryService

fornecedores_router = APIRouter(prefix="/api/fornecedores", tags=["fornecedores"])
categorias_router = APIRouter(prefix="/api/categorias", tags=["categorias"])
usuarios_router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@fornecedores_router.get("", response_model=list[str])
def listar_fornecedores() -> list[str]:
    """Lista fornecedores."""
    return FinancialEntryService().list_suppliers()


@categorias_router.get("", response_model=list[str])
def listar_categorias() -> list[str]:
    """Lista categorias."""
    return FinancialEntryService().list_categories()


@usuarios_router.get("", response_model=list[str])
def listar_usuarios() -> list[str]:
    """Lista usuarios."""
    return FinancialEntryService().list_users()
