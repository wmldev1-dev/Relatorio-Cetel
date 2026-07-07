"""Schemas de dados financeiros."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app.schemas.common import APIModel


class CompetenciaOption(APIModel):
    """Opcao de competencia para selecao."""

    id: int
    periodo: str


class LancamentoResponse(APIModel):
    """Lancamento financeiro consolidado."""

    data_lancamento: date | None = None
    data_pagamento: date | None = None
    documento: str | None = None
    tipo: str | None = None
    categoria: str | None = None
    servico: str | None = None
    fornecedor: str | None = None
    cidade: str | None = None
    centro_custo: str | None = None
    descricao: str | None = None
    valor: Decimal
    usuario: str | None = None
    arquivo_origem: str | None = None


class CompetenciaOverview(APIModel):
    """Resumo e lancamentos de uma competencia."""

    count: int
    total: Decimal
    entries: list[LancamentoResponse]


class LancamentosPaginados(APIModel):
    """Resposta paginada de lancamentos."""

    total: int
    limit: int
    offset: int
    items: list[LancamentoResponse]


class DashboardResponse(APIModel):
    """Resumo geral para dashboard."""

    competencias: int
    resumo_mensal: list[dict[str, Any]]
