"""Servico do dashboard financeiro executivo."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.database import Database
from app.models.competence import Competence
from app.models.financial_entry import FinancialEntry
from app.repositories.competence_repository import CompetenceRepository


class DashboardService:
    """Monta o dashboard executivo com consultas agregadas."""

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico com uma instancia de banco opcional."""
        self.database = database or Database()

    def get_executive_dashboard(
        self,
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
        """Retorna todos os blocos do dashboard executivo em uma chamada."""
        self.database.init_models()

        with self.database.get_session() as session:
            competences = CompetenceRepository(session).list_all()
            selected_competence = competencia or (competences[0].period if competences else None)
            previous_competence = self._previous_competence(competences, selected_competence)

            current_filters = DashboardFilters(
                competencia=selected_competence,
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
            previous_filters = current_filters.with_competencia(previous_competence)
            no_competence_filters = current_filters.with_competencia(None)

            month_total = self._total(session, current_filters)
            previous_month_total = self._total(session, previous_filters)
            general_total = self._total(session, no_competence_filters)
            entry_count = self._count(session, current_filters)

            categories = self._aggregate(session, current_filters, FinancialEntry.category, "categoria")
            suppliers = self._aggregate(session, current_filters, FinancialEntry.supplier, "fornecedor")
            services = self._aggregate(session, current_filters, FinancialEntry.service, "servico")
            cities = self._aggregate(session, current_filters, FinancialEntry.city, "cidade")
            monthly_evolution = self._monthly_evolution(session, current_filters)
            last_entries = self._last_entries(session, current_filters)

            return {
                "filters": {
                    "competencias": [{"periodo": item.period, "id": item.id} for item in competences],
                    "competencia_selecionada": selected_competence,
                    "competencia_anterior": previous_competence,
                    "fornecedores": self._distinct_values(session, FinancialEntry.supplier),
                    "categorias": self._distinct_values(session, FinancialEntry.category),
                    "servicos": self._distinct_values(session, FinancialEntry.service),
                    "cidades": self._distinct_values(session, FinancialEntry.city),
                    "centros_custo": self._distinct_values(session, FinancialEntry.cost_center),
                },
                "kpis": self._kpis(
                    general_total=general_total,
                    month_total=month_total,
                    previous_month_total=previous_month_total,
                    entry_count=entry_count,
                    supplier_count=self._distinct_count(session, current_filters, FinancialEntry.supplier),
                    category_count=self._distinct_count(session, current_filters, FinancialEntry.category),
                    service_count=self._distinct_count(session, current_filters, FinancialEntry.service),
                ),
                "charts": {
                    "evolucao_mensal": monthly_evolution,
                    "top_categorias": categories[:10],
                    "top_fornecedores": suppliers[:10],
                    "top_servicos": services[:10],
                    "distribuicao_categorias": self._with_share(categories),
                    "distribuicao_fornecedores": self._with_share(suppliers),
                    "comparacao_mensal": self._comparison(
                        selected_competence,
                        month_total,
                        previous_competence,
                        previous_month_total,
                    ),
                    "distribuicao_cidades": cities[:10],
                },
                "tables": {
                    "categorias": categories[:20],
                    "fornecedores": suppliers[:20],
                    "servicos": services[:20],
                    "ultimos_lancamentos": last_entries,
                },
                "insights": self._insights(
                    categories=categories,
                    suppliers=suppliers,
                    services=services,
                    last_entries=last_entries,
                    selected_competence=selected_competence,
                    previous_competence=previous_competence,
                    month_total=month_total,
                    previous_month_total=previous_month_total,
                ),
                "metadata": {
                    "ultima_atualizacao": self._last_update(session),
                    "gerado_em": datetime.utcnow().isoformat(),
                },
            }

    @staticmethod
    def _previous_competence(competences: list[Competence], selected: str | None) -> str | None:
        periods = [item.period for item in competences]
        if selected not in periods:
            return periods[1] if len(periods) > 1 else None
        index = periods.index(selected)
        return periods[index + 1] if index + 1 < len(periods) else None

    def _base_statement(self, filters: DashboardFilters) -> Select[tuple[FinancialEntry]]:
        statement = select(FinancialEntry).join(Competence)
        return self._apply_filters(statement, filters)

    def _apply_filters(self, statement: Select[Any], filters: DashboardFilters) -> Select[Any]:
        conditions = []
        if filters.competencia:
            conditions.append(Competence.period == filters.competencia)
        if filters.fornecedor:
            conditions.append(FinancialEntry.supplier == filters.fornecedor)
        if filters.categoria:
            conditions.append(FinancialEntry.category == filters.categoria)
        if filters.servico:
            conditions.append(FinancialEntry.service == filters.servico)
        if filters.cidade:
            conditions.append(FinancialEntry.city == filters.cidade)
        if filters.centro_custo:
            conditions.append(FinancialEntry.cost_center == filters.centro_custo)
        if filters.valor_inicial is not None:
            conditions.append(FinancialEntry.amount >= filters.valor_inicial)
        if filters.valor_final is not None:
            conditions.append(FinancialEntry.amount <= filters.valor_final)
        if filters.data_inicial:
            conditions.append(FinancialEntry.entry_date >= filters.data_inicial)
        if filters.data_final:
            conditions.append(FinancialEntry.entry_date <= filters.data_final)
        return statement.where(*conditions) if conditions else statement

    def _total(self, session: Session, filters: DashboardFilters) -> Decimal:
        statement = self._apply_filters(
            select(func.coalesce(func.sum(FinancialEntry.amount), 0)).join(Competence),
            filters,
        )
        return Decimal(session.scalar(statement) or 0)

    def _count(self, session: Session, filters: DashboardFilters) -> int:
        statement = self._apply_filters(
            select(func.count(FinancialEntry.id)).join(Competence),
            filters,
        )
        return int(session.scalar(statement) or 0)

    def _distinct_count(self, session: Session, filters: DashboardFilters, column: Any) -> int:
        statement = self._apply_filters(
            select(func.count(func.distinct(column))).join(Competence),
            filters,
        ).where(column.is_not(None), func.trim(column) != "")
        return int(session.scalar(statement) or 0)

    def _aggregate(
        self,
        session: Session,
        filters: DashboardFilters,
        column: Any,
        label: str,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        total = func.coalesce(func.sum(FinancialEntry.amount), 0)
        statement = self._apply_filters(
            select(
                column.label("name"),
                func.count(FinancialEntry.id).label("quantidade"),
                total.label("total"),
                func.coalesce(func.avg(FinancialEntry.amount), 0).label("ticket_medio"),
            ).join(Competence),
            filters,
        )
        statement = (
            statement.where(column.is_not(None), func.trim(column) != "")
            .group_by(column)
            .order_by(total.desc())
            .limit(limit)
        )
        rows = session.execute(statement).all()
        return [
            {
                label: str(row.name),
                "nome": str(row.name),
                "valor_total": Decimal(row.total or 0),
                "quantidade": int(row.quantidade or 0),
                "ticket_medio": Decimal(row.ticket_medio or 0),
            }
            for row in rows
        ]

    def _monthly_evolution(
        self,
        session: Session,
        filters: DashboardFilters,
    ) -> list[dict[str, object]]:
        monthly_filters = filters.with_competencia(None)
        total = func.coalesce(func.sum(FinancialEntry.amount), 0)
        statement = self._apply_filters(
            select(
                Competence.period.label("competencia"),
                func.count(FinancialEntry.id).label("quantidade"),
                total.label("total"),
            )
            .select_from(FinancialEntry)
            .join(Competence),
            monthly_filters,
        )
        statement = statement.group_by(Competence.period).order_by(Competence.period.asc())
        return [
            {
                "competencia": row.competencia,
                "quantidade": int(row.quantidade or 0),
                "total": Decimal(row.total or 0),
            }
            for row in session.execute(statement).all()
        ]

    def _last_entries(
        self,
        session: Session,
        filters: DashboardFilters,
        limit: int = 30,
    ) -> list[dict[str, object]]:
        statement = (
            self._base_statement(filters)
            .order_by(FinancialEntry.entry_date.desc(), FinancialEntry.id.desc())
            .limit(limit)
        )
        return [self._entry_to_dict(entry) for entry in session.scalars(statement).all()]

    @staticmethod
    def _distinct_values(session: Session, column: Any) -> list[str]:
        statement = (
            select(column)
            .where(column.is_not(None), func.trim(column) != "")
            .distinct()
            .order_by(column.asc())
        )
        return [str(value) for value in session.scalars(statement).all()]

    @staticmethod
    def _with_share(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        total = sum((Decimal(str(row["valor_total"])) for row in rows), Decimal("0.00"))
        if total == 0:
            return rows[:10]
        return [
            {
                **row,
                "percentual_sobre_total": Decimal(str(row["valor_total"])) / total * 100,
            }
            for row in rows[:10]
        ]

    @staticmethod
    def _comparison(
        selected_competence: str | None,
        month_total: Decimal,
        previous_competence: str | None,
        previous_month_total: Decimal,
    ) -> list[dict[str, object]]:
        return [
            {"competencia": previous_competence or "Mês anterior", "total": previous_month_total},
            {"competencia": selected_competence or "Competência atual", "total": month_total},
        ]

    @staticmethod
    def _kpis(
        general_total: Decimal,
        month_total: Decimal,
        previous_month_total: Decimal,
        entry_count: int,
        supplier_count: int,
        category_count: int,
        service_count: int,
    ) -> list[dict[str, object]]:
        ticket = month_total / entry_count if entry_count else Decimal("0.00")
        variation = DashboardService._variation(month_total, previous_month_total)
        return [
            {"key": "total_geral", "titulo": "TOTAL GERAL", "valor": general_total, "descricao": "Total filtrado em todas as competências", "icone": "R$", "variacao": variation},
            {"key": "total_mes", "titulo": "TOTAL DO MÊS", "valor": month_total, "descricao": "Total da competência selecionada", "icone": "M", "variacao": variation},
            {"key": "lancamentos", "titulo": "TOTAL DE LANÇAMENTOS", "valor": entry_count, "descricao": "Quantidade de pagamentos no filtro", "icone": "Q", "variacao": variation},
            {"key": "ticket_medio", "titulo": "TICKET MÉDIO", "valor": ticket, "descricao": "Valor médio por lançamento", "icone": "T", "variacao": variation},
            {"key": "fornecedores", "titulo": "TOTAL DE FORNECEDORES", "valor": supplier_count, "descricao": "Fornecedores distintos no filtro", "icone": "F", "variacao": variation},
            {"key": "categorias", "titulo": "TOTAL DE CATEGORIAS", "valor": category_count, "descricao": "Categorias distintas no filtro", "icone": "C", "variacao": variation},
            {"key": "servicos", "titulo": "TOTAL DE SERVIÇOS", "valor": service_count, "descricao": "Serviços distintos no filtro", "icone": "S", "variacao": variation},
        ]

    @staticmethod
    def _variation(current: Decimal, previous: Decimal) -> dict[str, object]:
        if previous == 0:
            percent = Decimal("0.00")
        else:
            percent = ((current - previous) / previous) * 100
        status = "aumento" if percent > 0 else "reducao" if percent < 0 else "estavel"
        return {
            "valor": current - previous,
            "percentual": percent,
            "status": status,
            "texto": f"{percent:.2f}%",
        }

    @staticmethod
    def _insights(
        categories: list[dict[str, object]],
        suppliers: list[dict[str, object]],
        services: list[dict[str, object]],
        last_entries: list[dict[str, object]],
        selected_competence: str | None,
        previous_competence: str | None,
        month_total: Decimal,
        previous_month_total: Decimal,
    ) -> list[dict[str, object]]:
        variation = DashboardService._variation(month_total, previous_month_total)
        biggest_entry = max(
            last_entries,
            key=lambda item: Decimal(str(item.get("valor") or 0)),
            default={},
        )
        return [
            {"titulo": "Variação mensal", "descricao": f"{selected_competence or 'Competência atual'} contra {previous_competence or 'mês anterior'}: {variation['texto']}.", "status": variation["status"]},
            {"titulo": "Fornecedor que mais recebeu", "descricao": DashboardService._leader_text(suppliers, "fornecedor"), "status": "neutral"},
            {"titulo": "Categoria com maior peso", "descricao": DashboardService._leader_text(categories, "categoria"), "status": "neutral"},
            {"titulo": "Serviço mais relevante", "descricao": DashboardService._leader_text(services, "servico"), "status": "neutral"},
            {"titulo": "Maior lançamento", "descricao": DashboardService._entry_text(biggest_entry), "status": "warning"},
            {"titulo": "Maior quantidade de pagamentos", "descricao": DashboardService._quantity_leader(suppliers), "status": "neutral"},
        ]

    @staticmethod
    def _leader_text(rows: list[dict[str, object]], key: str) -> str:
        if not rows:
            return "Sem dados suficientes no filtro atual."
        leader = rows[0]
        return (
            f"{leader.get(key) or leader.get('nome')} concentrou "
            f"{DashboardService._format_currency(leader.get('valor_total'))}."
        )

    @staticmethod
    def _quantity_leader(rows: list[dict[str, object]]) -> str:
        if not rows:
            return "Sem dados suficientes no filtro atual."
        leader = max(rows, key=lambda item: int(item.get("quantidade") or 0))
        return f"{leader.get('fornecedor') or leader.get('nome')} teve {leader.get('quantidade')} pagamentos."

    @staticmethod
    def _entry_text(entry: dict[str, object]) -> str:
        if not entry:
            return "Nenhum lançamento encontrado no filtro atual."
        return (
            f"{entry.get('fornecedor') or 'Sem fornecedor'}: "
            f"{DashboardService._format_currency(entry.get('valor'))}."
        )

    @staticmethod
    def _last_update(session: Session) -> str | None:
        value = session.scalar(select(func.max(FinancialEntry.updated_at)))
        if isinstance(value, datetime):
            return value.isoformat()
        return None

    @staticmethod
    def _format_currency(value: object) -> str:
        amount = Decimal(str(value or 0))
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _entry_to_dict(entry: FinancialEntry) -> dict[str, object]:
        return {
            "data_lancamento": entry.entry_date,
            "fornecedor": entry.supplier,
            "valor": entry.amount,
            "categoria": entry.category,
            "servico": entry.service,
            "cidade": entry.city,
            "centro_custo": entry.cost_center,
            "documento": entry.document_number,
            "descricao": entry.description,
        }


class DashboardFilters:
    """Filtros aplicados ao dashboard executivo."""

    def __init__(
        self,
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
    ) -> None:
        self.competencia = competencia
        self.fornecedor = fornecedor
        self.categoria = categoria
        self.servico = servico
        self.cidade = cidade
        self.centro_custo = centro_custo
        self.valor_inicial = valor_inicial
        self.valor_final = valor_final
        self.data_inicial = data_inicial
        self.data_final = data_final

    def with_competencia(self, competencia: str | None) -> DashboardFilters:
        """Clona filtros alterando apenas a competencia."""
        return DashboardFilters(
            competencia=competencia,
            fornecedor=self.fornecedor,
            categoria=self.categoria,
            servico=self.servico,
            cidade=self.cidade,
            centro_custo=self.centro_custo,
            valor_inicial=self.valor_inicial,
            valor_final=self.valor_final,
            data_inicial=self.data_inicial,
            data_final=self.data_final,
        )
