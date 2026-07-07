"""Repositorio para lancamentos financeiros consolidados."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.financial_entry import FinancialEntry


class FinancialEntryRepository:
    """Encapsula consultas e operacoes de lancamentos financeiros."""

    def __init__(self, session: Session) -> None:
        """Recebe uma sessao SQLAlchemy ativa."""
        self.session = session

    def count_by_competence(self, competence_id: int) -> int:
        """Conta lancamentos de uma competencia."""
        statement = select(func.count(FinancialEntry.id)).where(
            FinancialEntry.competence_id == competence_id,
        )
        return int(self.session.scalar(statement) or 0)

    def total_amount_by_competence(self, competence_id: int) -> Decimal:
        """Soma o valor dos lancamentos de uma competencia."""
        statement = select(func.coalesce(func.sum(FinancialEntry.amount), 0)).where(
            FinancialEntry.competence_id == competence_id,
        )
        return Decimal(self.session.scalar(statement) or 0)

    def aggregate_amount_by_field(
        self,
        competence_id: int,
        field: str,
    ) -> dict[str, Decimal]:
        """Soma valores por campo textual ignorando nomes vazios."""
        column = getattr(FinancialEntry, field)
        statement = (
            select(
                column.label("name"),
                func.coalesce(func.sum(FinancialEntry.amount), 0).label("total"),
            )
            .where(
                FinancialEntry.competence_id == competence_id,
                column.is_not(None),
                func.trim(column) != "",
                func.lower(func.trim(column)).not_in(("none", "null", "nan")),
            )
            .group_by(column)
        )
        rows = self.session.execute(statement).all()
        return {
            str(row.name).strip(): Decimal(row.total or 0)
            for row in rows
            if str(row.name).strip()
        }

    def list_by_competence(self, competence_id: int) -> list[FinancialEntry]:
        """Lista lancamentos de uma competencia."""
        statement = (
            select(FinancialEntry)
            .where(FinancialEntry.competence_id == competence_id)
            .order_by(
                FinancialEntry.entry_date.asc(),
                FinancialEntry.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())

    def count_all(self) -> int:
        """Conta todos os lancamentos financeiros."""
        statement = select(func.count(FinancialEntry.id))
        return int(self.session.scalar(statement) or 0)

    def list_all(self, limit: int = 500, offset: int = 0) -> list[FinancialEntry]:
        """Lista lancamentos financeiros consolidados."""
        statement = (
            select(FinancialEntry)
            .order_by(FinancialEntry.entry_date.desc(), FinancialEntry.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def list_distinct_values(self, field: str) -> list[str]:
        """Lista valores distintos nao vazios de um campo textual."""
        column = getattr(FinancialEntry, field)
        statement = (
            select(column)
            .where(column.is_not(None), column != "")
            .distinct()
            .order_by(column.asc())
        )
        return [str(value) for value in self.session.scalars(statement).all()]

    def count_by_import_batch(self, import_batch_id: int) -> int:
        """Conta lancamentos vinculados a um lote de importacao."""
        statement = select(func.count(FinancialEntry.id)).where(
            FinancialEntry.import_batch_id == import_batch_id,
        )
        return int(self.session.scalar(statement) or 0)

    def list_by_import_batch(
        self,
        import_batch_id: int,
        limit: int = 20,
    ) -> list[FinancialEntry]:
        """Lista lancamentos de um lote de importacao."""
        statement = (
            select(FinancialEntry)
            .where(FinancialEntry.import_batch_id == import_batch_id)
            .order_by(FinancialEntry.id.asc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def count_empty_fields_by_import_batch(
        self,
        import_batch_id: int,
        fields: list[str],
    ) -> dict[str, int]:
        """Conta campos importantes vazios por lote de importacao."""
        counts: dict[str, int] = {}
        for field in fields:
            column = getattr(FinancialEntry, field)
            if field == "amount":
                condition = or_(column.is_(None), column == 0)
            elif field in {"entry_date", "payment_date", "created_at_source"}:
                condition = column.is_(None)
            else:
                condition = or_(column.is_(None), column == "")

            statement = select(func.count(FinancialEntry.id)).where(
                FinancialEntry.import_batch_id == import_batch_id,
                condition,
            )
            counts[field] = int(self.session.scalar(statement) or 0)

        return counts

    def create_many(self, entries: list[dict[str, object]]) -> list[FinancialEntry]:
        """Cria varios lancamentos financeiros."""
        models = [FinancialEntry(**entry) for entry in entries]
        self.session.add_all(models)
        self.session.flush()
        return models

    def delete_by_import_batch(self, import_batch_id: int) -> int:
        """Remove lancamentos vinculados a um lote de importacao."""
        statement = delete(FinancialEntry).where(
            FinancialEntry.import_batch_id == import_batch_id,
        )
        result = self.session.execute(statement)
        return int(result.rowcount or 0)

    def get_monthly_summary(self) -> list[dict[str, object]]:
        """Retorna resumo mensal por competencia."""
        statement = (
            select(
                FinancialEntry.competence_id,
                func.count(FinancialEntry.id).label("entry_count"),
                func.coalesce(func.sum(FinancialEntry.amount), 0).label("total"),
            )
            .group_by(FinancialEntry.competence_id)
            .order_by(FinancialEntry.competence_id.asc())
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "competence_id": row.competence_id,
                "entry_count": int(row.entry_count or 0),
                "total": Decimal(row.total or 0),
            }
            for row in rows
        ]

    def get_supplier_summary_by_competence(
        self,
        competence_id: int,
    ) -> list[dict[str, object]]:
        """Retorna resumo por fornecedor em uma competencia."""
        statement = (
            select(
                FinancialEntry.supplier,
                func.count(FinancialEntry.id).label("entry_count"),
                func.coalesce(func.sum(FinancialEntry.amount), 0).label("total"),
            )
            .where(FinancialEntry.competence_id == competence_id)
            .group_by(FinancialEntry.supplier)
            .order_by(func.coalesce(func.sum(FinancialEntry.amount), 0).desc())
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "supplier": row.supplier,
                "entry_count": int(row.entry_count or 0),
                "total": Decimal(row.total or 0),
            }
            for row in rows
        ]

    def get_supplier_report_by_competence(
        self,
        competence_id: int,
        supplier: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """Retorna indicadores agregados por fornecedor."""
        conditions = [
            FinancialEntry.competence_id == competence_id,
            FinancialEntry.supplier.is_not(None),
            func.trim(FinancialEntry.supplier) != "",
            func.lower(func.trim(FinancialEntry.supplier)).not_in(
                ("none", "null", "nan"),
            ),
        ]
        if supplier:
            conditions.append(FinancialEntry.supplier == supplier)

        total = func.coalesce(func.sum(FinancialEntry.amount), 0)
        statement = (
            select(
                FinancialEntry.supplier.label("supplier"),
                func.count(FinancialEntry.id).label("entry_count"),
                total.label("total"),
                func.coalesce(func.avg(FinancialEntry.amount), 0).label("average"),
                func.coalesce(func.max(FinancialEntry.amount), 0).label("max_amount"),
                func.coalesce(func.min(FinancialEntry.amount), 0).label("min_amount"),
            )
            .where(*conditions)
            .group_by(FinancialEntry.supplier)
            .order_by(total.desc())
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "supplier": row.supplier,
                "entry_count": int(row.entry_count or 0),
                "total": Decimal(row.total or 0),
                "average": Decimal(row.average or 0),
                "max_amount": Decimal(row.max_amount or 0),
                "min_amount": Decimal(row.min_amount or 0),
            }
            for row in rows
        ]

    def get_service_report_by_competence(
        self,
        competence_id: int,
        service: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """Retorna indicadores agregados por servico."""
        conditions = [
            FinancialEntry.competence_id == competence_id,
            FinancialEntry.service.is_not(None),
            func.trim(FinancialEntry.service) != "",
            func.lower(func.trim(FinancialEntry.service)).not_in(
                ("none", "null", "nan"),
            ),
        ]
        if service:
            conditions.append(FinancialEntry.service == service)

        total = func.coalesce(func.sum(FinancialEntry.amount), 0)
        statement = (
            select(
                FinancialEntry.service.label("service"),
                func.count(FinancialEntry.id).label("entry_count"),
                total.label("total"),
                func.coalesce(func.avg(FinancialEntry.amount), 0).label("average"),
                func.coalesce(func.max(FinancialEntry.amount), 0).label("max_amount"),
                func.coalesce(func.min(FinancialEntry.amount), 0).label("min_amount"),
            )
            .where(*conditions)
            .group_by(FinancialEntry.service)
            .order_by(total.desc())
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "service": row.service,
                "entry_count": int(row.entry_count or 0),
                "total": Decimal(row.total or 0),
                "average": Decimal(row.average or 0),
                "max_amount": Decimal(row.max_amount or 0),
                "min_amount": Decimal(row.min_amount or 0),
            }
            for row in rows
        ]

    def get_service_summary_by_competence(
        self,
        competence_id: int,
    ) -> list[dict[str, object]]:
        """Retorna resumo por servico em uma competencia."""
        statement = (
            select(
                FinancialEntry.service,
                func.count(FinancialEntry.id).label("entry_count"),
                func.coalesce(func.sum(FinancialEntry.amount), 0).label("total"),
            )
            .where(FinancialEntry.competence_id == competence_id)
            .group_by(FinancialEntry.service)
            .order_by(func.coalesce(func.sum(FinancialEntry.amount), 0).desc())
        )
        rows = self.session.execute(statement).all()
        return [
            {
                "service": row.service,
                "entry_count": int(row.entry_count or 0),
                "total": Decimal(row.total or 0),
            }
            for row in rows
        ]
