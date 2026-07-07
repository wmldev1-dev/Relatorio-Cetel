"""Repositorio para lotes de importacao."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.competence import Competence
from app.models.import_batch import ImportBatch


class ImportRepository:
    """Encapsula operacoes de persistencia de importacoes."""

    def __init__(self, session: Session) -> None:
        """Recebe uma sessao SQLAlchemy ativa."""
        self.session = session

    def has_active_import_for_competence(self, competence_id: int) -> bool:
        """Indica se a competencia ja possui importacao ativa."""
        statement = select(ImportBatch.id).where(
            ImportBatch.competence_id == competence_id,
            ImportBatch.status.in_(ImportBatch.ACTIVE_STATUSES),
        )
        return self.session.scalar(statement) is not None

    def get_by_id(self, import_batch_id: int) -> ImportBatch | None:
        """Busca uma importacao pelo identificador."""
        statement = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.competence))
            .where(ImportBatch.id == import_batch_id)
        )
        return self.session.scalar(statement)

    def create(
        self,
        competence: Competence,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        status: str = ImportBatch.STATUS_PENDING,
        error_message: str | None = None,
    ) -> ImportBatch:
        """Registra um novo lote de importacao."""
        import_batch = ImportBatch(
            competence=competence,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            status=status,
            error_message=error_message,
        )
        self.session.add(import_batch)
        self.session.flush()
        return import_batch

    def update_status(
        self,
        import_batch: ImportBatch,
        status: str,
        error_message: str | None = None,
    ) -> ImportBatch:
        """Atualiza status e mensagem de erro de uma importacao."""
        import_batch.status = status
        import_batch.error_message = error_message
        self.session.flush()
        return import_batch

    def list_all(self) -> list[ImportBatch]:
        """Lista todas as importacoes registradas."""
        statement = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.competence))
            .join(ImportBatch.competence)
            .order_by(Competence.period.desc(), ImportBatch.imported_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def count_by_competence(self, competence_id: int) -> int:
        """Conta importacoes vinculadas a uma competencia."""
        statement = select(func.count(ImportBatch.id)).where(
            ImportBatch.competence_id == competence_id,
        )
        return int(self.session.scalar(statement) or 0)

    def get_latest_by_competence_period(self, period: str) -> ImportBatch | None:
        """Busca o lote mais recente de uma competencia."""
        statement = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.competence))
            .join(ImportBatch.competence)
            .where(Competence.period == period)
            .order_by(ImportBatch.imported_at.desc(), ImportBatch.id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def delete(self, import_batch: ImportBatch) -> None:
        """Remove um lote de importacao."""
        self.session.delete(import_batch)
        self.session.flush()
