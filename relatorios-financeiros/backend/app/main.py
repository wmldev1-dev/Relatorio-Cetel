"""Aplicacao FastAPI dos relatorios financeiros."""

from __future__ import annotations

import logging

from fastapi import Depends
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.cadastros import categorias_router, fornecedores_router, usuarios_router
from app.api.comparativo import router as comparativo_router
from app.api.dashboard import router as dashboard_router
from app.api.diagnostico import router as diagnostico_router
from app.api.importacoes import router as importacoes_router
from app.api.lancamentos import router as lancamentos_router
from app.api.relatorios import router as relatorios_router
from app.api.users import router as users_router
from app.core.dependencies import require_active_user
from app.core.settings import settings
from app.database.database import Database
from app.schemas.common import HealthResponse
from app.services.auth_service import AuthService
from app.services.rbac_service import RBACService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("relatorios_financeiros.api")

app = FastAPI(title="Relatorios Financeiros API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

protected_dependencies = [Depends(require_active_user)]

app.include_router(auth_router)
app.include_router(importacoes_router, dependencies=protected_dependencies)
app.include_router(lancamentos_router, dependencies=protected_dependencies)
app.include_router(fornecedores_router, dependencies=protected_dependencies)
app.include_router(categorias_router, dependencies=protected_dependencies)
app.include_router(dashboard_router, dependencies=protected_dependencies)
app.include_router(usuarios_router, dependencies=protected_dependencies)
app.include_router(diagnostico_router, dependencies=protected_dependencies)
app.include_router(comparativo_router, dependencies=protected_dependencies)
app.include_router(relatorios_router, dependencies=protected_dependencies)
app.include_router(users_router, dependencies=protected_dependencies)


@app.on_event("startup")
def startup() -> None:
    """Inicializa tabelas e usuario admin inicial."""
    if settings.jwt_secret_key == "troque-esta-chave":
        logger.warning(
            "JWT_SECRET_KEY está usando o valor padrão. Altere em produção.",
        )
    RBACService().seed_defaults()
    Database().ensure_user_management_columns()
    created, message = AuthService().seed_initial_admin()
    if created:
        logger.info(message)
    else:
        logger.info(message)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Registra e normaliza erros de validacao."""
    logger.warning("Erro de validação em %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Parâmetros inválidos. Revise os filtros informados.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Registra erros inesperados sem expor detalhes internos."""
    logger.exception("Erro inesperado em %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno ao processar a solicitação."},
    )


def _healthcheck() -> HealthResponse:
    """Testa a disponibilidade da API e do banco."""
    is_connected, message = Database().test_connection()
    return HealthResponse(
        status="ok" if is_connected else "error",
        database=message,
    )


@app.get("/api/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    """Testa a disponibilidade da API e do banco."""
    return _healthcheck()


@app.get("/health", response_model=HealthResponse)
def root_healthcheck() -> HealthResponse:
    """Testa a disponibilidade da API e do banco."""
    return _healthcheck()
