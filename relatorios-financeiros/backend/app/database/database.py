"""Infraestrutura de conexao com banco de dados."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import settings


class Base(DeclarativeBase):
    """Base declarativa dos modelos ORM da aplicacao."""


class Database:
    """Gerencia a criacao e validacao da conexao com o MySQL."""

    def __init__(self) -> None:
        """Inicializa o gerenciador sem abrir conexao imediatamente."""
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    def get_engine(self) -> Engine:
        """Retorna uma engine SQLAlchemy reutilizavel."""
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL não configurada.")

        if self._engine is None:
            self._engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=settings.pool_size,
                max_overflow=settings.max_overflow,
                pool_recycle=settings.pool_recycle,
                pool_timeout=settings.pool_timeout,
                future=True,
            )

        return self._engine

    def get_session(self) -> Session:
        """Retorna uma nova sessao SQLAlchemy."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(),
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
                future=True,
            )

        return self._session_factory()

    def init_models(self) -> None:
        """Cria as tabelas da aplicacao, se necessario."""
        from app.models import (  # noqa: F401
            Competence,
            FinancialEntry,
            ImportBatch,
            Permission,
            Role,
            RolePermission,
            User,
            UserAuditLog,
            UserRole,
        )

        Base.metadata.create_all(self.get_engine())

    def ensure_user_management_columns(self) -> None:
        """Adiciona colunas administrativas em bases existentes."""
        engine = self.get_engine()
        inspector = inspect(engine)
        existing = {column["name"] for column in inspector.get_columns("users")}
        columns = {
            "last_login_at": "DATETIME NULL",
            "created_by_id": "INT NULL",
            "updated_by_id": "INT NULL",
            "failed_login_attempts": "INT NOT NULL DEFAULT 0",
            "first_failed_login_at": "DATETIME NULL",
            "locked_until": "DATETIME NULL",
        }
        with engine.begin() as connection:
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE users ADD COLUMN {column_name} {definition}"),
                    )

    def test_connection(self) -> tuple[bool, str]:
        """Testa a conexao com o banco de dados."""
        try:
            engine = self.get_engine()
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return True, "Conexão realizada com sucesso."
        except SQLAlchemyError as error:
            return False, f"Erro ao conectar ao banco de dados: {error}"
