"""Schemas de relatorios financeiros."""

from __future__ import annotations

from decimal import Decimal

from app.schemas.common import APIModel


class RelatorioFornecedorItem(APIModel):
    """Resumo de gastos por fornecedor."""

    fornecedor: str
    total: Decimal
    quantidade_lancamentos: int
    ticket_medio: Decimal
    percentual_sobre_total: Decimal
    maior_lancamento: Decimal
    menor_lancamento: Decimal


class RelatorioServicoItem(APIModel):
    """Resumo de gastos por servico."""

    servico: str
    total: Decimal
    quantidade_lancamentos: int
    ticket_medio: Decimal
    percentual_sobre_total: Decimal
    maior_lancamento: Decimal
    menor_lancamento: Decimal
