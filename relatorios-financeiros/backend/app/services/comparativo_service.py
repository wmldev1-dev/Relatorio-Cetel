"""Servicos para comparativos financeiros mensais."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from app.database.database import Database
from app.repositories.competence_repository import CompetenceRepository
from app.repositories.financial_entry_repository import FinancialEntryRepository
from app.schemas.comparativo import ComparativoMensalResponse, ComparativoRankingItem
from app.services.competence_service import CompetenceService

ComparativoStatus = Literal["aumento", "reducao", "estavel"]


class ComparativoService:
    """Calcula comparativos entre duas competencias mensais."""

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico com uma instancia de banco opcional."""
        self.database = database or Database()
        self.competence_service = CompetenceService(self.database)

    def get_comparativo_mensal(
        self,
        competencia_base: str,
        competencia_comparacao: str,
    ) -> ComparativoMensalResponse:
        """Compara totais e rankings entre duas competencias."""
        base_period = self._validate_competence(competencia_base)
        comparison_period = self._validate_competence(competencia_comparacao)
        self.database.init_models()

        with self.database.get_session() as session:
            competence_repository = CompetenceRepository(session)
            entry_repository = FinancialEntryRepository(session)
            base = competence_repository.get_by_period(base_period)
            comparison = competence_repository.get_by_period(comparison_period)

            base_id = base.id if base else None
            comparison_id = comparison.id if comparison else None

            total_base = (
                entry_repository.total_amount_by_competence(base_id)
                if base_id is not None
                else Decimal("0.00")
            )
            total_comparison = (
                entry_repository.total_amount_by_competence(comparison_id)
                if comparison_id is not None
                else Decimal("0.00")
            )
            count_base = (
                entry_repository.count_by_competence(base_id)
                if base_id is not None
                else 0
            )
            count_comparison = (
                entry_repository.count_by_competence(comparison_id)
                if comparison_id is not None
                else 0
            )

            supplier_rankings = self._build_rankings(
                entry_repository,
                base_id,
                comparison_id,
                "supplier",
            )
            service_rankings = self._build_rankings(
                entry_repository,
                base_id,
                comparison_id,
                "service",
            )
            category_rankings = self._build_rankings(
                entry_repository,
                base_id,
                comparison_id,
                "category",
            )

        difference = total_comparison - total_base
        return ComparativoMensalResponse(
            competencia_base=base_period,
            competencia_comparacao=comparison_period,
            total_base=total_base,
            total_comparacao=total_comparison,
            diferenca_valor=difference,
            diferenca_percentual=self._percentage_difference(total_base, total_comparison),
            status=self._status(difference),
            total_lancamentos_base=count_base,
            total_lancamentos_comparacao=count_comparison,
            fornecedores_maior_aumento=supplier_rankings["aumentos"],
            fornecedores_maior_reducao=supplier_rankings["reducoes"],
            servicos_maior_aumento=service_rankings["aumentos"],
            servicos_maior_reducao=service_rankings["reducoes"],
            categorias_maior_aumento=category_rankings["aumentos"],
            categorias_maior_reducao=category_rankings["reducoes"],
        )

    def _validate_competence(self, value: str) -> str:
        is_valid, result = self.competence_service.validate_competence(value)
        if not is_valid:
            raise ValueError(result)
        return result

    def _build_rankings(
        self,
        repository: FinancialEntryRepository,
        base_id: int | None,
        comparison_id: int | None,
        field: str,
    ) -> dict[str, list[ComparativoRankingItem]]:
        base_values = (
            repository.aggregate_amount_by_field(base_id, field)
            if base_id is not None
            else {}
        )
        comparison_values = (
            repository.aggregate_amount_by_field(comparison_id, field)
            if comparison_id is not None
            else {}
        )
        names = sorted(set(base_values) | set(comparison_values))
        items = [
            self._ranking_item(
                name,
                base_values.get(name, Decimal("0.00")),
                comparison_values.get(name, Decimal("0.00")),
            )
            for name in names
        ]
        increases = sorted(
            items,
            key=lambda item: item.diferenca_valor,
            reverse=True,
        )[:10]
        reductions = sorted(items, key=lambda item: item.diferenca_valor)[:10]
        return {"aumentos": increases, "reducoes": reductions}

    def _ranking_item(
        self,
        name: str,
        base_value: Decimal,
        comparison_value: Decimal,
    ) -> ComparativoRankingItem:
        difference = comparison_value - base_value
        return ComparativoRankingItem(
            nome=name,
            valor_base=base_value,
            valor_comparacao=comparison_value,
            diferenca_valor=difference,
            diferenca_percentual=self._percentage_difference(
                base_value,
                comparison_value,
            ),
            status=self._status(difference),
        )

    @staticmethod
    def _percentage_difference(base_value: Decimal, comparison_value: Decimal) -> Decimal:
        difference = comparison_value - base_value
        if base_value > 0:
            return (difference / base_value * Decimal("100")).quantize(Decimal("0.01"))
        if comparison_value > 0:
            return Decimal("100.00")
        return Decimal("0.00")

    @staticmethod
    def _status(difference: Decimal) -> ComparativoStatus:
        if difference > 0:
            return "aumento"
        if difference < 0:
            return "reducao"
        return "estavel"
