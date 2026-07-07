"""Modelo de competencia mensal."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Competence(Base):
    """Representa uma competencia mensal no formato YYYY-MM."""

    __tablename__ = "competences"
    __table_args__ = (
        UniqueConstraint("period", name="uq_competences_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    import_batches: Mapped[list["ImportBatch"]] = relationship(
        "ImportBatch",
        back_populates="competence",
        cascade="all, delete-orphan",
    )
    financial_entries: Mapped[list["FinancialEntry"]] = relationship(
        "FinancialEntry",
        back_populates="competence",
        cascade="all, delete-orphan",
    )
