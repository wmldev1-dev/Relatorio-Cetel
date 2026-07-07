"""Servicos de relatorio por fornecedor."""

from __future__ import annotations

from decimal import Decimal

from app.database.database import Database
from app.repositories.competence_repository import CompetenceRepository
from app.repositories.financial_entry_repository import FinancialEntryRepository
from app.schemas.relatorios import RelatorioFornecedorItem
from app.services.competence_service import CompetenceService


class RelatorioFornecedorService:
    """Gera analises de gastos por fornecedor."""

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico com uma instancia de banco opcional."""
        self.database = database or Database()
        self.competence_service = CompetenceService(self.database)

    def listar_fornecedores(
        self,
        competencia: str,
        fornecedor: str | None = None,
        limit: int = 50,
    ) -> list[RelatorioFornecedorItem]:
        """Lista indicadores por fornecedor dentro de uma competencia."""
        is_valid, normalized_competence = self.competence_service.validate_competence(
            competencia,
        )
        if not is_valid:
            raise ValueError(normalized_competence)

        self.database.init_models()
        with self.database.get_session() as session:
            competence_repository = CompetenceRepository(session)
            entry_repository = FinancialEntryRepository(session)
            competence = competence_repository.get_by_period(normalized_competence)
            if competence is None:
                return []

            total_competence = entry_repository.total_amount_by_competence(
                competence.id,
            )
            rows = entry_repository.get_supplier_report_by_competence(
                competence_id=competence.id,
                supplier=fornecedor,
                limit=max(1, min(limit, 500)),
            )

        return [
            RelatorioFornecedorItem(
                fornecedor=str(row["supplier"]),
                total=Decimal(row["total"]),
                quantidade_lancamentos=int(row["entry_count"]),
                ticket_medio=Decimal(row["average"]).quantize(Decimal("0.01")),
                percentual_sobre_total=self._percentage(
                    Decimal(row["total"]),
                    total_competence,
                ),
                maior_lancamento=Decimal(row["max_amount"]),
                menor_lancamento=Decimal(row["min_amount"]),
            )
            for row in rows
        ]

    @staticmethod
    def _percentage(value: Decimal, total: Decimal) -> Decimal:
        if total > 0:
            return (value / total * Decimal("100")).quantize(Decimal("0.01"))
        return Decimal("0.00")
