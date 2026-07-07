"""Diagnostico de preenchimento dos campos financeiros."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.core.settings import settings
from app.database.database import Database
from app.models.financial_entry import FinancialEntry
from app.repositories.competence_repository import CompetenceRepository
from app.repositories.financial_entry_repository import FinancialEntryRepository
from app.repositories.import_repository import ImportRepository
from app.services.competence_service import CompetenceService
from app.services.import_processor_service import ImportProcessorService
from app.services.sql_parser_service import SQLParserService


class DiagnosticoCamposService:
    """Gera diagnostico de campos vazios por competencia."""

    FIELDS: tuple[str, ...] = (
        "supplier",
        "service",
        "category",
        "city",
        "cost_center",
        "description",
        "amount",
        "entry_date",
    )

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa dependencias do diagnostico."""
        self.database = database or Database()
        self.competence_service = CompetenceService(self.database)
        self.parser = SQLParserService()
        self.import_processor = ImportProcessorService(self.database)

    def diagnosticar(self, competencia: str) -> dict[str, object]:
        """Retorna diagnostico de preenchimento para uma competencia."""
        is_valid, normalized_competence = self.competence_service.validate_competence(
            competencia,
        )
        if not is_valid:
            raise ValueError(normalized_competence)

        self.database.init_models()
        with self.database.get_session() as session:
            competence_repository = CompetenceRepository(session)
            import_repository = ImportRepository(session)
            entry_repository = FinancialEntryRepository(session)
            competence = competence_repository.get_by_period(normalized_competence)
            entries = (
                entry_repository.list_by_competence(competence.id)
                if competence is not None
                else []
            )
            latest_import = import_repository.get_latest_by_competence_period(
                normalized_competence,
            )

        parsed_records = self._parse_import_records(latest_import)
        parse_summary = self.parser.get_parse_summary()
        unmapped_fields = self.import_processor.get_unmapped_fields(parsed_records)

        return {
            "competencia": normalized_competence,
            "total_lancamentos": len(entries),
            "preenchimento": self._field_fill_rates(entries),
            "amostra_registros_originais": self._sample_original_records(parsed_records),
            "amostra_lancamentos_gravados": [
                self._entry_to_dict(entry)
                for entry in entries[:20]
            ],
            "colunas_origem_detectadas": parse_summary.get("columns", []),
            "tabelas_origem_detectadas": parse_summary.get("tables", []),
            "campos_nao_mapeados": unmapped_fields,
            "sugestoes_campos_servico": self._suggest_service_candidates(
                parse_summary.get("columns", []),
                unmapped_fields,
            ),
        }

    def _parse_import_records(self, import_batch: Any | None) -> list[dict[str, Any]]:
        if import_batch is None:
            return []

        file_path = settings.backend_dir / import_batch.file_path
        if not file_path.exists():
            return []

        return self.parser.parse_file(file_path)

    def _field_fill_rates(
        self,
        entries: list[FinancialEntry],
    ) -> list[dict[str, object]]:
        total = len(entries)
        result = []
        for field in self.FIELDS:
            filled = sum(1 for entry in entries if not self._is_empty(entry, field))
            empty = total - filled
            percentage = (
                Decimal(filled) / Decimal(total) * Decimal("100")
                if total
                else Decimal("0")
            )
            result.append(
                {
                    "campo": field,
                    "quantidade_preenchida": filled,
                    "quantidade_vazia": empty,
                    "percentual_preenchido": percentage.quantize(Decimal("0.01")),
                },
            )
        return result

    def _sample_original_records(
        self,
        records: list[dict[str, Any]],
        limit: int = 20,
    ) -> list[dict[str, object]]:
        samples = []
        for record in records:
            if str(record.get("_source_table", "")).lower() in {
                "categorias",
                "fornecedores",
                "usuarios",
            }:
                continue

            clean_record = {
                key: value
                for key, value in record.items()
                if not key.startswith("_")
            }
            clean_record["tabela_origem"] = record.get("_source_table", "")
            samples.append(clean_record)
            if len(samples) >= limit:
                break
        return samples

    @staticmethod
    def _suggest_service_candidates(
        columns: list[str],
        unmapped_fields: list[str],
    ) -> list[str]:
        keywords = (
            "serv",
            "produto",
            "item",
            "descricao",
            "descri",
            "historico",
            "categoria",
            "tipo",
            "nome",
        )
        candidates = {
            column
            for column in [*columns, *unmapped_fields]
            if any(keyword in column.lower() for keyword in keywords)
        }
        return sorted(candidates)

    @staticmethod
    def _is_empty(entry: FinancialEntry, field: str) -> bool:
        value = getattr(entry, field)
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip().lower() in {"", "none", "null", "nan"}
        if field == "amount":
            return Decimal(value or 0) == 0
        return False

    @staticmethod
    def _entry_to_dict(entry: FinancialEntry) -> dict[str, object]:
        return {
            "id": entry.id,
            "supplier": entry.supplier,
            "service": entry.service,
            "category": entry.category,
            "city": entry.city,
            "cost_center": entry.cost_center,
            "description": entry.description,
            "amount": entry.amount,
            "entry_date": entry.entry_date,
            "source_file": entry.source_file,
        }
