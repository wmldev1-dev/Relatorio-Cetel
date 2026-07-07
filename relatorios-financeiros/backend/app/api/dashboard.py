"""Rotas de dashboard."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter

from app.schemas.financeiro import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.services.financial_entry_service import FinancialEntryService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def listar_dashboard() -> dict[str, object]:
    """Retorna indicadores consolidados."""
    return FinancialEntryService().get_dashboard()


@router.get("/financeiro", response_model=dict[str, Any])
def listar_dashboard_financeiro(
    competence_id: int | None = None,
    fornecedor: str | None = None,
    categoria: str | None = None,
    usuario: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    valor_minimo: Decimal | None = None,
    valor_maximo: Decimal | None = None,
) -> dict[str, object]:
    """Retorna dashboard financeiro filtrado."""
    return FinancialEntryService().get_financial_dashboard(
        competence_id=competence_id,
        supplier=fornecedor,
        category=categoria,
        user_name=usuario,
        start_date=data_inicio,
        end_date=data_fim,
        min_amount=valor_minimo,
        max_amount=valor_maximo,
    )


@router.get("/executivo", response_model=dict[str, Any])
def listar_dashboard_executivo(
    competencia: str | None = None,
    fornecedor: str | None = None,
    categoria: str | None = None,
    servico: str | None = None,
    cidade: str | None = None,
    centro_custo: str | None = None,
    valor_inicial: Decimal | None = None,
    valor_final: Decimal | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> dict[str, object]:
    """Retorna o dashboard executivo completo em uma unica chamada."""
    return DashboardService().get_executive_dashboard(
        competencia=competencia,
        fornecedor=fornecedor,
        categoria=categoria,
        servico=servico,
        cidade=cidade,
        centro_custo=centro_custo,
        valor_inicial=valor_inicial,
        valor_final=valor_final,
        data_inicial=data_inicial,
        data_final=data_final,
    )
