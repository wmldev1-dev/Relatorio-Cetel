"""Repositorio para competencias mensais."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competence import Competence


class CompetenceRepository:
    """Encapsula operacoes de persistencia de competencias."""

    def __init__(self, session: Session) -> None:
        """Recebe uma sessao SQLAlchemy ativa."""
        self.session = session

    def get_by_period(self, period: str) -> Competence | None:
        """Busca uma competencia pelo periodo YYYY-MM."""
        statement = select(Competence).where(Competence.period == period)
        return self.session.scalar(statement)

    def list_all(self) -> list[Competence]:
        """Lista todas as competencias cadastradas."""
        statement = select(Competence).order_by(Competence.period.desc())
        return list(self.session.scalars(statement).all())

    def create(self, period: str) -> Competence:
        """Cria uma nova competencia mensal."""
        competence = Competence(period=period)
        self.session.add(competence)
        self.session.flush()
        return competence

    def get_or_create(self, period: str) -> Competence:
        """Retorna uma competencia existente ou cria uma nova."""
        competence = self.get_by_period(period)
        if competence is not None:
            return competence

        return self.create(period)

    def delete(self, competence: Competence) -> None:
        """Remove uma competencia mensal."""
        self.session.delete(competence)
        self.session.flush()
