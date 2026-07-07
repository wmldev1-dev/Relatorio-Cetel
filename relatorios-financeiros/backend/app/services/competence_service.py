"""Servicos de validacao e consulta de competencias."""

from __future__ import annotations

import re
from datetime import datetime

from app.database.database import Database
from app.repositories.competence_repository import CompetenceRepository


class CompetenceService:
    """Concentra regras de negocio relacionadas a competencias mensais."""

    _COMPETENCE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

    def __init__(self, database: Database | None = None) -> None:
        """Inicializa o servico com uma instancia de banco opcional."""
        self.database = database or Database()

    def validate_competence(self, competence: str) -> tuple[bool, str]:
        """Valida se a competencia esta no formato YYYY-MM."""
        normalized_competence = competence.strip()
        if not normalized_competence:
            return False, "Informe a competência."

        if not self._COMPETENCE_PATTERN.match(normalized_competence):
            return False, "A competência deve estar no formato YYYY-MM."

        try:
            datetime.strptime(normalized_competence, "%Y-%m")
        except ValueError:
            return False, "A competência informada é inválida."

        return True, normalized_competence

    def get_or_create_competence(self, competence: str) -> int:
        """Cria a competencia se necessario e retorna seu identificador."""
        self.database.init_models()

        with self.database.get_session() as session:
            repository = CompetenceRepository(session)
            model = repository.get_or_create(competence)
            session.commit()
            return model.id
