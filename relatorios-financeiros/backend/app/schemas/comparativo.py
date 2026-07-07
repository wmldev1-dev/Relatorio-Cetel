"""Schemas do comparativo mensal."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from app.schemas.common import APIModel

ComparativoStatus = Literal["aumento", "reducao", "estavel"]


class ComparativoRankingItem(APIModel):
    """Item de ranking do comparativo mensal."""

    nome: str
    valor_base: Decimal
    valor_comparacao: Decimal
    diferenca_valor: Decimal
    diferenca_percentual: Decimal
    status: ComparativoStatus


class ComparativoMensalResponse(APIModel):
    """Resposta consolidada do comparativo mensal."""

    competencia_base: str
    competencia_comparacao: str
    total_base: Decimal
    total_comparacao: Decimal
    diferenca_valor: Decimal
    diferenca_percentual: Decimal
    status: ComparativoStatus
    total_lancamentos_base: int
    total_lancamentos_comparacao: int
    fornecedores_maior_aumento: list[ComparativoRankingItem]
    fornecedores_maior_reducao: list[ComparativoRankingItem]
    servicos_maior_aumento: list[ComparativoRankingItem]
    servicos_maior_reducao: list[ComparativoRankingItem]
    categorias_maior_aumento: list[ComparativoRankingItem]
    categorias_maior_reducao: list[ComparativoRankingItem]
