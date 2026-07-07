"""Rotas de comparativos financeiros."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.permissions import require_permission
from app.schemas.comparativo import ComparativoMensalResponse
from app.services.comparativo_service import ComparativoService

router = APIRouter(prefix="/api/comparativo", tags=["comparativo"])


@router.get(
    "/mensal",
    response_model=ComparativoMensalResponse,
    dependencies=[Depends(require_permission("comparativo.view"))],
)
def obter_comparativo_mensal(
    competencia_base: str,
    competencia_comparacao: str,
) -> ComparativoMensalResponse:
    """Retorna comparativo financeiro entre duas competencias."""
    try:
        return ComparativoService().get_comparativo_mensal(
            competencia_base=competencia_base,
            competencia_comparacao=competencia_comparacao,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
