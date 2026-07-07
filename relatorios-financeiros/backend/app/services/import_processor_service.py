"""Processamento de arquivos SQL importados."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.database.database import Database
from app.core.settings import settings
from app.models.import_batch import ImportBatch
from app.repositories.financial_entry_repository import FinancialEntryRepository
from app.repositories.import_repository import ImportRepository
from app.services.financial_entry_service import FinancialEntryService
from app.services.financial_mapping_service import FinancialMappingService
from app.services.raw_financial_parser_service import RawFinancialParserService
from app.services.sql_parser_service import SQLParserService


class ImportProcessorService:
    """Processa lotes SQL e grava lancamentos financeiros consolidados."""

    IMPORTANT_FIELDS: tuple[str, ...] = (
        "supplier",
        "service",
        "category",
        "amount",
        "entry_date",
    )

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa dependencias do processamento."""
        self.database = database or Database()
        self.parser = SQLParserService()
        self.raw_parser = RawFinancialParserService()
        self.entry_service = FinancialEntryService(self.database)
        self.mapping_service = FinancialMappingService()
        self.logger = self._create_logger()

    def process_import(self, import_batch_id: int) -> tuple[bool, str]:
        """Processa um lote de importacao e grava financial_entries."""
        self.database.init_models()
        self.logger.info(
            "Iniciando processamento do import_batch_id=%s",
            import_batch_id,
        )

        try:
            with self.database.get_session() as session:
                import_repository = ImportRepository(session)
                entry_repository = FinancialEntryRepository(session)
                import_batch = import_repository.get_by_id(import_batch_id)

                if import_batch is None:
                    return False, "Importação não encontrada."

                file_path = settings.backend_dir / import_batch.file_path
                if not file_path.exists():
                    message = f"Arquivo SQL não encontrado: {import_batch.file_path}"
                    import_repository.update_status(
                        import_batch,
                        ImportBatch.STATUS_FAILED,
                        message,
                    )
                    session.commit()
                    self.logger.error(message)
                    return False, message

                parser = self._get_parser(file_path)
                parsed_records = parser.parse_file(file_path)
                if not parsed_records:
                    message = "Nenhum lançamento válido foi encontrado no arquivo."
                    import_repository.update_status(
                        import_batch,
                        ImportBatch.STATUS_FAILED,
                        message,
                    )
                    session.commit()
                    self.logger.warning(message)
                    return False, message

                entry_repository.delete_by_import_batch(import_batch.id)
                prepared_entries = self._prepare_entries(import_batch, parsed_records)
                if not prepared_entries:
                    message = "Nenhum lançamento financeiro pôde ser mapeado."
                    import_repository.update_status(
                        import_batch,
                        ImportBatch.STATUS_FAILED,
                        message,
                    )
                    session.commit()
                    self.logger.warning(message)
                    return False, message

                entry_repository.create_many(prepared_entries)
                import_repository.update_status(
                    import_batch,
                    ImportBatch.STATUS_IMPORTED,
                )
                session.commit()

                message = (
                    f"Processamento concluído: {len(prepared_entries)} "
                    "lançamentos gravados."
                )
                self.logger.info(message)
                return True, message
        except (OSError, SQLAlchemyError, ValueError) as error:
            self.logger.exception(
                "Falha ao processar import_batch_id=%s",
                import_batch_id,
            )
            self._mark_failed(import_batch_id, str(error))
            return False, f"Erro ao processar SQL: {error}"

    def reprocess_import(self, import_batch_id: int) -> tuple[bool, str]:
        """Reprocessa um lote ja importado recriando seus lancamentos."""
        return self.process_import(import_batch_id)

    def get_import_diagnostics(self, import_batch_id: int) -> dict[str, object]:
        """Retorna diagnostico completo de parse e gravacao de uma importacao."""
        self.database.init_models()

        with self.database.get_session() as session:
            import_repository = ImportRepository(session)
            entry_repository = FinancialEntryRepository(session)
            import_batch = import_repository.get_by_id(import_batch_id)

            if import_batch is None:
                raise ValueError("Importação não encontrada.")

            file_path = settings.backend_dir / import_batch.file_path
            parser = self._get_parser(file_path)
            parsed_records = parser.parse_file(file_path) if file_path.exists() else []
            parse_summary = parser.get_parse_summary()
            saved_entries = entry_repository.list_by_import_batch(
                import_batch.id,
                limit=20,
            )
            saved_count = entry_repository.count_by_import_batch(import_batch.id)

            return {
                "import_batch_id": import_batch.id,
                "status": import_batch.status,
                "source_file": import_batch.stored_filename,
                "file_path": import_batch.file_path,
                "file_exists": file_path.exists(),
                "competence": import_batch.competence.period,
                "insert_count": parse_summary["insert_count"],
                "extracted_count": parse_summary["record_count"],
                "saved_count": saved_count,
                "tables": parse_summary["tables"],
                "columns": parse_summary["columns"],
                "extracted_preview": parser.preview_records(limit=20),
                "saved_preview": [
                    self._financial_entry_to_dict(entry)
                    for entry in saved_entries
                ],
                "unmapped_fields": self.get_unmapped_fields(parsed_records),
                "empty_important_fields": self.get_empty_important_fields(
                    parsed_records,
                    entry_repository,
                    import_batch.id,
                ),
                "error_message": import_batch.error_message or "",
            }

    def get_unmapped_fields(self, records: list[dict[str, Any]]) -> list[str]:
        """Lista campos extraidos que nao possuem alias para financial_entries."""
        return self.mapping_service.get_unmapped_fields(records)

    def get_empty_important_fields(
        self,
        records: list[dict[str, Any]],
        entry_repository: FinancialEntryRepository,
        import_batch_id: int,
    ) -> list[dict[str, int | str]]:
        """Compara vazios importantes extraidos e gravados."""
        lookup_context = self.mapping_service.build_lookup_context(records)
        saved_counts = entry_repository.count_empty_fields_by_import_batch(
            import_batch_id,
            list(self.IMPORTANT_FIELDS),
        )
        extracted_counts = {
            field: self._count_empty_mapped_field(records, field, lookup_context)
            for field in self.IMPORTANT_FIELDS
        }

        return [
            {
                "campo": field,
                "vazios_extraidos": extracted_counts[field],
                "vazios_gravados": saved_counts[field],
            }
            for field in self.IMPORTANT_FIELDS
        ]

    def _prepare_entries(
        self,
        import_batch: ImportBatch,
        parsed_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Mapeia registros do parser para financial_entries."""
        entries: list[dict[str, Any]] = []
        lookup_context = self.mapping_service.build_lookup_context(parsed_records)
        for record in parsed_records:
            mapped = self.mapping_service.map_record(record, lookup_context)
            if not mapped:
                continue

            mapped["competence_id"] = import_batch.competence_id
            mapped["import_batch_id"] = import_batch.id
            mapped["source_file"] = import_batch.stored_filename

            prepared = self.entry_service.prepare_entry(mapped)
            is_valid, message = self.entry_service.validate_entry(prepared)
            if not is_valid:
                raise ValueError(message)

            entries.append(prepared)

        return entries

    def _get_parser(self, file_path: Any) -> SQLParserService | RawFinancialParserService:
        """Escolhe parser SQL ou bruto conforme extensao/conteudo."""
        if str(file_path).lower().endswith(".sql"):
            return self.parser

        return self.raw_parser

    def _count_empty_mapped_field(
        self,
        records: list[dict[str, Any]],
        field: str,
        lookup_context: dict[str, dict[str, dict[str, Any]]],
    ) -> int:
        """Conta registros extraidos sem valor para um campo mapeado."""
        aliases = self.mapping_service.FIELD_ALIASES[field]
        empty_count = 0

        for record in records:
            if str(record.get("_source_table", "")).lower() in {
                "categorias",
                "fornecedores",
                "usuarios",
            }:
                continue

            mapped = self.mapping_service.map_record(record, lookup_context)
            value = mapped.get(field)
            if value in (None, ""):
                empty_count += 1
                continue

            if field == "amount" and str(value).strip() in {"", "0", "0.00"}:
                empty_count += 1
                continue

            if not any(
                self.mapping_service.normalize_key(alias)
                in {self.mapping_service.normalize_key(key) for key in record}
                for alias in aliases
            ):
                empty_count += 1

        return empty_count

    @staticmethod
    def _financial_entry_to_dict(entry: Any) -> dict[str, object]:
        """Converte lancamento gravado em dicionario para diagnostico."""
        return {
            "id": entry.id,
            "entry_date": entry.entry_date,
            "payment_date": entry.payment_date,
            "document_number": entry.document_number,
            "transaction_type": entry.transaction_type,
            "category": entry.category,
            "service": entry.service,
            "supplier": entry.supplier,
            "supplier_type": entry.supplier_type,
            "city": entry.city,
            "cost_center": entry.cost_center,
            "description": entry.description,
            "amount": entry.amount,
            "user_name": entry.user_name,
            "source_file": entry.source_file,
        }

    def _mark_failed(self, import_batch_id: int, error_message: str) -> None:
        """Marca o lote como failed apos erro inesperado."""
        try:
            with self.database.get_session() as session:
                repository = ImportRepository(session)
                import_batch = repository.get_by_id(import_batch_id)
                if import_batch is None:
                    return

                repository.update_status(
                    import_batch,
                    ImportBatch.STATUS_FAILED,
                    error_message[:2000],
                )
                session.commit()
        except SQLAlchemyError:
            self.logger.exception(
                "Nao foi possivel marcar import_batch_id=%s como failed",
                import_batch_id,
            )

    def _create_logger(self) -> logging.Logger:
        """Cria logger de processamento de importacoes."""
        log_dir = settings.logs_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger("relatorios_financeiros.imports")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler(
                log_dir / "imports.log",
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(message)s",
                ),
            )
            logger.addHandler(handler)

        return logger
