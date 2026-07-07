"""Modelo consolidado de lancamentos financeiros."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class FinancialEntry(Base):
    """Representa um lancamento financeiro padronizado importado."""

    __tablename__ = "financial_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competence_id: Mapped[int] = mapped_column(
        ForeignKey("competences.id"),
        nullable=False,
        index=True,
    )
    import_batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batches.id"),
        nullable=False,
        index=True,
    )
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at_source: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    user_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    competence: Mapped["Competence"] = relationship(
        "Competence",
        back_populates="financial_entries",
    )
    import_batch: Mapped["ImportBatch"] = relationship(
        "ImportBatch",
        back_populates="financial_entries",
    )
