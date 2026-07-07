"""Rotas de relatorios financeiros."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.permissions import require_permission
from app.schemas.relatorios import RelatorioFornecedorItem, RelatorioServicoItem
from app.services.relatorio_fornecedor_service import RelatorioFornecedorService
from app.services.relatorio_servico_service import RelatorioServicoService

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


@router.get(
    "/fornecedores",
    response_model=list[RelatorioFornecedorItem],
    dependencies=[Depends(require_permission("fornecedores.view"))],
)
def listar_relatorio_fornecedores(
    competencia: str,
    fornecedor: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RelatorioFornecedorItem]:
    """Retorna gastos agregados por fornecedor em uma competencia."""
    try:
        return RelatorioFornecedorService().listar_fornecedores(
            competencia=competencia,
            fornecedor=fornecedor,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/servicos",
    response_model=list[RelatorioServicoItem],
    dependencies=[Depends(require_permission("servicos.view"))],
)
def listar_relatorio_servicos(
    competencia: str,
    servico: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[RelatorioServicoItem]:
    """Retorna gastos agregados por servico em uma competencia."""
    try:
        return RelatorioServicoService().listar_servicos(
            competencia=competencia,
            servico=servico,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
