"""Servicos para registro de importacoes mensais."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.exc import SQLAlchemyError

from app.database.database import Database
from app.core.settings import settings
from app.models.import_batch import ImportBatch
from app.repositories.competence_repository import CompetenceRepository
from app.repositories.financial_entry_repository import FinancialEntryRepository
from app.repositories.import_repository import ImportRepository
from app.services.competence_service import CompetenceService


class ImportService:
    """Orquestra validacao, armazenamento e registro de arquivos SQL."""

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico de importacao."""
        self.database = database or Database()
        self.competence_service = CompetenceService(self.database)
        self.import_dir = settings.imports_dir

    def register_import(
        self,
        competence: str,
        uploaded_file: BinaryIO | None,
    ) -> tuple[bool, str, int | None]:
        """Registra um arquivo SQL recebido para uma competencia mensal."""
        is_valid, competence_or_error = self.competence_service.validate_competence(
            competence,
        )
        if not is_valid:
            return False, competence_or_error, None

        if uploaded_file is None:
            return False, "Selecione um arquivo SQL.", None

        original_filename = getattr(uploaded_file, "name", "")
        is_valid_file, file_message = self._validate_sql_file(original_filename)
        if not is_valid_file:
            return False, file_message, None

        content = uploaded_file.read()
        if not content:
            return False, "O arquivo SQL não pode estar vazio.", None

        sanitized_filename = self.sanitize_filename(original_filename)
        stored_filename = f"{competence_or_error}_{sanitized_filename}"
        destination = self.import_dir / stored_filename

        try:
            self.database.init_models()
            self.import_dir.mkdir(parents=True, exist_ok=True)

            with self.database.get_session() as session:
                competence_repository = CompetenceRepository(session)
                import_repository = ImportRepository(session)
                competence_model = competence_repository.get_or_create(
                    competence_or_error,
                )

                if import_repository.has_active_import_for_competence(
                    competence_model.id,
                ):
                    session.rollback()
                    return (
                        False,
                        "Já existe uma importação ativa para esta competência.",
                        None,
                    )

                destination.write_bytes(content)
                import_batch = import_repository.create(
                    competence=competence_model,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_path=str(destination.relative_to(settings.backend_dir)),
                    status=ImportBatch.STATUS_PENDING,
                )
                session.commit()

            return True, "Importação registrada com status pending.", import_batch.id
        except SQLAlchemyError as error:
            return False, f"Erro ao registrar importação: {error}", None
        except OSError as error:
            return False, f"Erro ao salvar arquivo SQL: {error}", None

    def list_imports(self) -> list[dict[str, str]]:
        """Lista importacoes registradas para exibicao."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = ImportRepository(session)
            imports = repository.list_all()

            return [
                {
                    "competencia": item.competence.period,
                    "id_importacao": str(item.id),
                    "arquivo_original": item.original_filename,
                    "arquivo_salvo": item.stored_filename,
                    "status": item.status,
                    "data_importacao": item.imported_at.strftime(
                        "%Y-%m-%d %H:%M:%S",
                    ),
                    "erro": item.error_message or "",
                }
                for item in imports
            ]

    def get_import(self, import_batch_id: int) -> dict[str, str]:
        """Busca uma importacao registrada para exibicao."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = ImportRepository(session)
            item = repository.get_by_id(import_batch_id)
            if item is None:
                raise ValueError("Importação não encontrada.")

            return {
                "competencia": item.competence.period,
                "id_importacao": str(item.id),
                "arquivo_original": item.original_filename,
                "arquivo_salvo": item.stored_filename,
                "status": item.status,
                "data_importacao": item.imported_at.strftime("%Y-%m-%d %H:%M:%S"),
                "erro": item.error_message or "",
            }

    def delete_import(self, import_batch_id: int) -> tuple[bool, str]:
        """Remove uma importacao e seus lancamentos financeiros do banco."""
        self.database.init_models()

        try:
            with self.database.get_session() as session:
                competence_repository = CompetenceRepository(session)
                import_repository = ImportRepository(session)
                entry_repository = FinancialEntryRepository(session)
                import_batch = import_repository.get_by_id(import_batch_id)
                if import_batch is None:
                    raise ValueError("Importação não encontrada.")

                competence_model = import_batch.competence
                competence = import_batch.competence.period
                deleted_entries = entry_repository.delete_by_import_batch(import_batch.id)
                import_repository.delete(import_batch)
                deleted_competence = self._delete_orphan_competence(
                    competence_repository,
                    import_repository,
                    entry_repository,
                    competence_model,
                )
                session.commit()

            competence_message = (
                " Competência removida por não possuir outros lotes ou lançamentos."
                if deleted_competence
                else ""
            )
            return (
                True,
                (
                    f"Importação {import_batch_id} da competência {competence} "
                    f"removida. Lançamentos apagados: {deleted_entries}."
                    f"{competence_message}"
                ),
            )
        except SQLAlchemyError as error:
            return False, f"Erro ao remover importação: {error}"

    def _delete_orphan_competence(
        self,
        competence_repository: CompetenceRepository,
        import_repository: ImportRepository,
        entry_repository: FinancialEntryRepository,
        competence: object,
    ) -> bool:
        """Remove a competencia somente se ela ficou sem dependencias."""
        competence_id = getattr(competence, "id")
        has_imports = import_repository.count_by_competence(competence_id) > 0
        has_entries = entry_repository.count_by_competence(competence_id) > 0
        if has_imports or has_entries:
            return False

        competence_repository.delete(competence)
        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caracteres inseguros do nome do arquivo."""
        normalized = unicodedata.normalize("NFKD", filename)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name)
        safe_name = re.sub(r"-+", "-", safe_name).strip(".-_")
        return safe_name.lower() or "arquivo.sql"

    @staticmethod
    def _validate_sql_file(filename: str) -> tuple[bool, str]:
        """Valida extensao e nome do arquivo enviado."""
        if not filename:
            return False, "O arquivo deve possuir um nome válido."

        allowed_suffixes = {"", ".sql", ".txt", ".tsv", ".csv"}
        if Path(filename).suffix.lower() not in allowed_suffixes:
            return False, "O arquivo deve ser .sql, .txt, .tsv, .csv ou sem extensão."

        return True, "Arquivo válido."
