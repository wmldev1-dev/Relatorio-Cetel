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
    admin_name: str = getenv("ADMIN_NAME", "Administrador")
    admin_email: str = getenv("ADMIN_EMAIL", "admin@cetel.local")
    admin_password: str = getenv("ADMIN_PASSWORD", "")
    jwt_secret_key: str = getenv("JWT_SECRET_KEY", getenv("SECRET_KEY", "troque-esta-chave"))
    jwt_algorithm: str = getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(
        getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"),
    )
    pool_size: int = int(getenv("DB_POOL_SIZE", "5"))
    max_overflow: int = int(getenv("DB_MAX_OVERFLOW", "10"))
    pool_recycle: int = int(getenv("DB_POOL_RECYCLE", "3600"))
    pool_timeout: int = int(getenv("DB_POOL_TIMEOUT", "30"))
    backend_dir: Path = BACKEND_DIR
    imports_dir: Path = BASE_DIR / "storage" / "sql" / "imports"
    logs_dir: Path = BASE_DIR / "logs"


settings = Settings()
