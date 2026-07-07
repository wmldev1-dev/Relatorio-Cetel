"""Modelo de lote de importacao mensal."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ImportBatch(Base):
    """Controla um arquivo SQL recebido para uma competencia."""

    __tablename__ = "import_batches"

    STATUS_PENDING: ClassVar[str] = "pending"
    STATUS_IMPORTED: ClassVar[str] = "imported"
    STATUS_FAILED: ClassVar[str] = "failed"
    STATUS_REPLACED: ClassVar[str] = "replaced"
    ACTIVE_STATUSES: ClassVar[set[str]] = {STATUS_PENDING, STATUS_IMPORTED}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competence_id: Mapped[int] = mapped_column(
        ForeignKey("competences.id"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=STATUS_PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    competence: Mapped["Competence"] = relationship(
        "Competence",
        back_populates="import_batches",
    )
    financial_entries: Mapped[list["FinancialEntry"]] = relationship(
        "FinancialEntry",
        back_populates="import_batch",
        cascade="all, delete-orphan",
    )
