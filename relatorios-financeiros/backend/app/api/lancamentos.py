"""Rotas de lancamentos financeiros."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.financeiro import (
    CompetenciaOption,
    CompetenciaOverview,
    LancamentoResponse,
    LancamentosPaginados,
)
from app.services.financial_entry_service import FinancialEntryService

router = APIRouter(prefix="/api/lancamentos", tags=["lancamentos"])


@router.get("", response_model=list[LancamentoResponse])
def listar_lancamentos(
    limit: int = Query(default=500, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, object]]:
    """Lista lancamentos consolidados."""
    return FinancialEntryService().list_entries(limit=limit, offset=offset)


@router.get("/paginado", response_model=LancamentosPaginados)
def listar_lancamentos_paginados(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    """Lista lancamentos consolidados com metadados de paginacao."""
    return FinancialEntryService().list_entries_paginated(
        limit=limit,
        offset=offset,
    )


@router.get("/competencias", response_model=list[CompetenciaOption])
def listar_competencias() -> list[CompetenciaOption]:
    """Lista competencias disponiveis."""
    options = FinancialEntryService().get_competence_options()
    return [
        CompetenciaOption(id=competence_id, periodo=period)
        for competence_id, period in options
    ]


@router.get("/competencias/{competence_id}", response_model=CompetenciaOverview)
def obter_competencia(competence_id: int) -> dict[str, object]:
    """Retorna resumo e lancamentos de uma competencia."""
    return FinancialEntryService().get_competence_overview(competence_id)
