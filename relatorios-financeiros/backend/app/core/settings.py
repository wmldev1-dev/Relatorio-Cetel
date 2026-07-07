"""Configuracoes centrais do backend."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent
BASE_DIR = BACKEND_DIR
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Representa as configuracoes carregadas do ambiente."""

    database_url: str = getenv("DATABASE_URL", "")
    secret_key: str = getenv("SECRET_KEY", "change-me")
    pool_size: int = int(getenv("DB_POOL_SIZE", "5"))
    max_overflow: int = int(getenv("DB_MAX_OVERFLOW", "10"))
    pool_recycle: int = int(getenv("DB_POOL_RECYCLE", "3600"))
    pool_timeout: int = int(getenv("DB_POOL_TIMEOUT", "30"))
    backend_dir: Path = BACKEND_DIR
    imports_dir: Path = BASE_DIR / "storage" / "sql" / "imports"
    logs_dir: Path = BASE_DIR / "logs"


settings = Settings()
