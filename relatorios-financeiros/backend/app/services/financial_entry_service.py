"""Servicos para lancamentos financeiros consolidados."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from numbers import Number
from typing import Any

from app.database.database import Database
from app.models.financial_entry import FinancialEntry
from app.repositories.competence_repository import CompetenceRepository
from app.repositories.financial_entry_repository import FinancialEntryRepository


class FinancialEntryService:
    """Concentra regras de normalizacao e consulta de lancamentos."""

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico com uma instancia de banco opcional."""
        self.database = database or Database()

    def normalize_amount(self, value: Any) -> Decimal:
        """Normaliza valores monetarios para Decimal com duas casas."""
        if value is None or value == "":
            return Decimal("0.00")

        if isinstance(value, Decimal):
            return value.quantize(Decimal("0.01"))

        if isinstance(value, Number):
            return Decimal(str(value)).quantize(Decimal("0.01"))

        normalized = str(value).strip()
        if "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")

        try:
            return Decimal(normalized).quantize(Decimal("0.01"))
        except InvalidOperation as error:
            raise ValueError("Valor financeiro inválido.") from error

    def normalize_text(self, value: Any) -> str | None:
        """Normaliza textos vazios para None e remove espacos externos."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    def prepare_entry(self, data: dict[str, Any]) -> dict[str, Any]:
        """Prepara dados brutos para criacao de FinancialEntry."""
        return {
            "competence_id": data.get("competence_id"),
            "import_batch_id": data.get("import_batch_id"),
            "entry_date": self._normalize_date(data.get("entry_date")),
            "payment_date": self._normalize_date(data.get("payment_date")),
            "created_at_source": self._normalize_datetime(
                data.get("created_at_source"),
            ),
            "document_number": self.normalize_text(data.get("document_number")),
            "transaction_type": self.normalize_text(data.get("transaction_type")),
            "category": self.normalize_text(data.get("category")),
            "service": self.normalize_text(data.get("service")),
            "supplier": self.normalize_text(data.get("supplier")),
            "supplier_type": self.normalize_text(data.get("supplier_type")),
            "city": self.normalize_text(data.get("city")),
            "cost_center": self.normalize_text(data.get("cost_center")),
            "description": self.normalize_text(data.get("description")),
            "amount": self.normalize_amount(data.get("amount")),
            "user_name": self.normalize_text(data.get("user_name")),
            "source_file": self.normalize_text(data.get("source_file")),
        }

    def validate_entry(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Valida os campos obrigatorios de um lancamento preparado."""
        if not data.get("competence_id"):
            return False, "O lançamento deve possuir uma competência."

        if not data.get("import_batch_id"):
            return False, "O lançamento deve possuir um lote de importação."

        try:
            self.normalize_amount(data.get("amount"))
        except ValueError as error:
            return False, str(error)

        return True, "Lançamento válido."

    def get_competence_options(self) -> list[tuple[int, str]]:
        """Lista competencias disponiveis para selecao."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = CompetenceRepository(session)
            competences = repository.list_all()
            return [(item.id, item.period) for item in competences]

    def get_competence_overview(
        self,
        competence_id: int,
    ) -> dict[str, object]:
        """Retorna indicadores e lancamentos de uma competencia."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = FinancialEntryRepository(session)
            entries = repository.list_by_competence(competence_id)

            return {
                "count": repository.count_by_competence(competence_id),
                "total": repository.total_amount_by_competence(competence_id),
                "entries": [self._entry_to_dict(entry) for entry in entries],
            }

    def list_entries(
        self,
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict[str, object]]:
        """Lista lancamentos consolidados para a API."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = FinancialEntryRepository(session)
            return [
                self._entry_to_dict(entry)
                for entry in repository.list_all(limit=limit, offset=offset)
            ]

    def list_entries_paginated(self, limit: int = 100, offset: int = 0) -> dict[str, object]:
        """Lista lancamentos com metadados de paginacao."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = FinancialEntryRepository(session)
            total = repository.count_all()
            entries = repository.list_all(limit=limit, offset=offset)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [self._entry_to_dict(entry) for entry in entries],
        }

    def list_suppliers(self) -> list[str]:
        """Lista fornecedores encontrados nos lancamentos."""
        return self._list_distinct("supplier")

    def list_categories(self) -> list[str]:
        """Lista categorias encontradas nos lancamentos."""
        return self._list_distinct("category")

    def list_users(self) -> list[str]:
        """Lista usuarios encontrados nos lancamentos."""
        return self._list_distinct("user_name")

    def get_dashboard(self) -> dict[str, object]:
        """Retorna indicadores consolidados para dashboard."""
        self.database.init_models()

        with self.database.get_session() as session:
            competence_repository = CompetenceRepository(session)
            entry_repository = FinancialEntryRepository(session)
            competences = competence_repository.list_all()
            monthly_summary = entry_repository.get_monthly_summary()

            monthly_by_competence = {
                item["competence_id"]: item
                for item in monthly_summary
            }
            resumo_mensal = [
                {
                    "competencia": competence.period,
                    "quantidade": monthly_by_competence.get(
                        competence.id,
                        {},
                    ).get("entry_count", 0),
                    "total": monthly_by_competence.get(
                        competence.id,
                        {},
                    ).get("total", Decimal("0.00")),
                }
                for competence in competences
            ]

            return {
                "competencias": len(competences),
                "resumo_mensal": resumo_mensal,
            }

    def get_financial_dashboard(
        self,
        competence_id: int | None = None,
        supplier: str | None = None,
        category: str | None = None,
        user_name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
    ) -> dict[str, object]:
        """Retorna dados filtrados e agregados para o dashboard financeiro."""
        self.database.init_models()

        with self.database.get_session() as session:
            competence_repository = CompetenceRepository(session)
            entry_repository = FinancialEntryRepository(session)
            competences = competence_repository.list_all()
            entries = entry_repository.list_all(limit=10000)

        filtered_entries = [
            entry for entry in entries
            if self._matches_dashboard_filters(
                entry,
                competence_id,
                supplier,
                category,
                user_name,
                start_date,
                end_date,
                min_amount,
                max_amount,
            )
        ]
        entry_dicts = [self._entry_to_dict(entry) for entry in filtered_entries]
        total = sum((entry.amount for entry in filtered_entries), Decimal("0.00"))

        return {
            "filters": {
                "competencias": [
                    {"id": competence.id, "periodo": competence.period}
                    for competence in competences
                ],
                "fornecedores": self._distinct_from_entries(entries, "supplier"),
                "categorias": self._distinct_from_entries(entries, "category"),
                "usuarios": self._distinct_from_entries(entries, "user_name"),
            },
            "metricas": {
                "quantidade": len(filtered_entries),
                "total": total,
                "ticket_medio": (
                    total / len(filtered_entries)
                    if filtered_entries
                    else Decimal("0.00")
                ),
                "maior_despesa": max(
                    (entry.amount for entry in filtered_entries),
                    default=Decimal("0.00"),
                ),
            },
            "por_fornecedor": self._aggregate_entries(filtered_entries, "supplier"),
            "por_categoria": self._aggregate_entries(filtered_entries, "category"),
            "por_usuario": self._aggregate_entries(filtered_entries, "user_name"),
            "por_dia": self._aggregate_entries_by_day(filtered_entries),
            "maiores_despesas": [
                self._entry_to_dict(entry)
                for entry in sorted(
                    filtered_entries,
                    key=lambda item: item.amount,
                    reverse=True,
                )[:20]
            ],
            "lancamentos": entry_dicts,
        }

    def _list_distinct(self, field: str) -> list[str]:
        """Lista valores distintos de um campo de lancamento."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = FinancialEntryRepository(session)
            return repository.list_distinct_values(field)

    @staticmethod
    def _matches_dashboard_filters(
        entry: FinancialEntry,
        competence_id: int | None,
        supplier: str | None,
        category: str | None,
        user_name: str | None,
        start_date: date | None,
        end_date: date | None,
        min_amount: Decimal | None,
        max_amount: Decimal | None,
    ) -> bool:
        """Aplica filtros do dashboard em memoria."""
        if competence_id and entry.competence_id != competence_id:
            return False
        if supplier and entry.supplier != supplier:
            return False
        if category and entry.category != category:
            return False
        if user_name and entry.user_name != user_name:
            return False
        if start_date and (entry.entry_date is None or entry.entry_date < start_date):
            return False
        if end_date and (entry.entry_date is None or entry.entry_date > end_date):
            return False
        if min_amount is not None and entry.amount < min_amount:
            return False
        if max_amount is not None and entry.amount > max_amount:
            return False
        return True

    @staticmethod
    def _distinct_from_entries(entries: list[FinancialEntry], field: str) -> list[str]:
        """Lista valores distintos a partir dos lancamentos carregados."""
        values = {
            str(value)
            for entry in entries
            if (value := getattr(entry, field)) not in (None, "")
        }
        return sorted(values)

    @staticmethod
    def _aggregate_entries(
        entries: list[FinancialEntry],
        field: str,
    ) -> list[dict[str, object]]:
        """Agrega lancamentos por campo textual."""
        grouped: dict[str, dict[str, object]] = {}
        for entry in entries:
            label = str(getattr(entry, field) or "Sem informação")
            item = grouped.setdefault(
                label,
                {"nome": label, "quantidade": 0, "total": Decimal("0.00")},
            )
            item["quantidade"] = int(item["quantidade"]) + 1
            item["total"] = Decimal(item["total"]) + entry.amount

        return sorted(
            grouped.values(),
            key=lambda item: Decimal(item["total"]),
            reverse=True,
        )

    @staticmethod
    def _aggregate_entries_by_day(
        entries: list[FinancialEntry],
    ) -> list[dict[str, object]]:
        """Agrega lancamentos por data."""
        grouped: dict[str, dict[str, object]] = {}
        for entry in entries:
            label = (
                entry.entry_date.isoformat()
                if entry.entry_date is not None
                else "Sem data"
            )
            item = grouped.setdefault(
                label,
                {"data": label, "quantidade": 0, "total": Decimal("0.00")},
            )
            item["quantidade"] = int(item["quantidade"]) + 1
            item["total"] = Decimal(item["total"]) + entry.amount

        return sorted(grouped.values(), key=lambda item: str(item["data"]))

    @staticmethod
    def _normalize_date(value: Any) -> date | None:
        """Normaliza datas opcionais."""
        if value in (None, ""):
            return None

        if isinstance(value, date) and not isinstance(value, datetime):
            return value

        if isinstance(value, datetime):
            return value.date()

        normalized = str(value).strip()
        if normalized.upper() in {"CURRENT_TIMESTAMP", "NOW()"}:
            return None

        if normalized.startswith("0000-00-00"):
            return None

        for date_format in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(normalized, date_format).date()
            except ValueError:
                continue

        return datetime.fromisoformat(normalized).date()

    @staticmethod
    def _normalize_datetime(value: Any) -> datetime | None:
        """Normaliza data e hora opcionais."""
        if value in (None, ""):
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        normalized = str(value).strip()
        if normalized.upper() in {"CURRENT_TIMESTAMP", "NOW()"}:
            return None

        if normalized.startswith("0000-00-00"):
            return None

        for date_format in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M:%S",
        ):
            try:
                return datetime.strptime(normalized, date_format)
            except ValueError:
                continue

        return datetime.fromisoformat(normalized)

    @staticmethod
    def _entry_to_dict(entry: FinancialEntry) -> dict[str, object]:
        """Converte um lancamento em dicionario para exibicao."""
        return {
            "data_lancamento": entry.entry_date,
            "data_pagamento": entry.payment_date,
            "documento": entry.document_number,
            "tipo": entry.transaction_type,
            "categoria": entry.category,
            "servico": entry.service,
            "fornecedor": entry.supplier,
            "cidade": entry.city,
            "centro_custo": entry.cost_center,
            "descricao": entry.description,
            "valor": entry.amount,
            "usuario": entry.user_name,
            "arquivo_origem": entry.source_file,
        }
