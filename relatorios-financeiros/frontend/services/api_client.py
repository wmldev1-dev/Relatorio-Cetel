"""Cliente HTTP para a API FastAPI."""

from __future__ import annotations

from os import getenv
from pathlib import Path
from typing import Any, BinaryIO

import requests
import streamlit as st
from dotenv import load_dotenv

FRONTEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = FRONTEND_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(FRONTEND_DIR / ".env")

API_URL = getenv("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 60


class APIClientError(RuntimeError):
    """Erro retornado pela API."""


class APIUnauthorizedError(APIClientError):
    """Erro de autenticacao expirada ou ausente."""


def login(email: str, password: str) -> dict[str, Any]:
    """Autentica usuario na API."""
    return _request(
        "POST",
        "/api/auth/login",
        json={"email": email, "password": password},
        authenticated=False,
    )


def get_me() -> dict[str, Any]:
    """Retorna usuario autenticado."""
    return _request("GET", "/api/auth/me")


def get_auth_permissions() -> dict[str, Any]:
    """Retorna papeis e permissoes do usuario autenticado."""
    return _request("GET", "/api/auth/permissions")


def logout() -> dict[str, Any]:
    """Executa logout logico."""
    return _request("POST", "/api/auth/logout", authenticated=False)


def testar_conexao() -> dict[str, Any]:
    """Testa a saude da API."""
    return _request("GET", "/api/health", authenticated=False)


def listar_importacoes() -> list[dict[str, Any]]:
    """Lista importacoes."""
    return _request("GET", "/api/importacoes")


def criar_importacao(competencia: str, arquivo: BinaryIO) -> dict[str, Any]:
    """Cria uma importacao enviando arquivo SQL."""
    if arquivo is None:
        raise APIClientError("Selecione um arquivo SQL.")

    files = {
        "arquivo": (
            getattr(arquivo, "name", "arquivo.sql"),
            arquivo,
            "application/sql",
        ),
    }
    return _request(
        "POST",
        "/api/importacoes",
        data={"competencia": competencia},
        files=files,
    )


def buscar_importacao(import_batch_id: int) -> dict[str, Any]:
    """Busca uma importacao."""
    return _request("GET", f"/api/importacoes/{import_batch_id}")


def processar_importacao(import_batch_id: int) -> dict[str, Any]:
    """Processa uma importacao."""
    return _request("POST", f"/api/importacoes/{import_batch_id}/processar")


def reprocessar_importacao(import_batch_id: int) -> dict[str, Any]:
    """Reprocessa uma importacao existente."""
    return _request("POST", f"/api/importacoes/{import_batch_id}/reprocessar")


def remover_importacao(import_batch_id: int) -> dict[str, Any]:
    """Remove uma importacao e seus lancamentos."""
    return _request("DELETE", f"/api/importacoes/{import_batch_id}")


def listar_lancamentos(limit: int = 500) -> list[dict[str, Any]]:
    """Lista lancamentos."""
    return _request("GET", "/api/lancamentos", params={"limit": limit})


def listar_lancamentos_paginados(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Lista lancamentos com metadados de paginacao."""
    return _request(
        "GET",
        "/api/lancamentos/paginado",
        params={"limit": limit, "offset": offset},
    )


def listar_competencias() -> list[dict[str, Any]]:
    """Lista competencias."""
    return _request("GET", "/api/lancamentos/competencias")


def obter_competencia(competence_id: int) -> dict[str, Any]:
    """Retorna resumo de uma competencia."""
    return _request("GET", f"/api/lancamentos/competencias/{competence_id}")


def listar_fornecedores() -> list[str]:
    """Lista fornecedores."""
    return _request("GET", "/api/fornecedores")


def listar_categorias() -> list[str]:
    """Lista categorias."""
    return _request("GET", "/api/categorias")


def listar_dashboard() -> dict[str, Any]:
    """Lista indicadores de dashboard."""
    return _request("GET", "/api/dashboard")


def listar_dashboard_financeiro(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lista dados agregados do dashboard financeiro."""
    clean_params = {
        key: value
        for key, value in (params or {}).items()
        if value not in (None, "", "Todos", "Todas")
    }
    return _request("GET", "/api/dashboard/financeiro", params=clean_params)


def listar_dashboard_executivo(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lista todos os blocos do dashboard executivo."""
    clean_params = {
        key: value
        for key, value in (params or {}).items()
        if value not in (None, "", "Todos", "Todas")
    }
    return _request("GET", "/api/dashboard/executivo", params=clean_params)


def listar_usuarios() -> list[str]:
    """Lista usuarios."""
    return _request("GET", "/api/usuarios")


def admin_listar_usuarios(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lista usuarios do painel administrativo."""
    clean_params = {
        key: value
        for key, value in (params or {}).items()
        if value not in (None, "", "Todos", "Todas")
    }
    return _request("GET", "/api/users", params=clean_params)


def admin_obter_usuario(user_id: int) -> dict[str, Any]:
    """Busca usuario administrativo."""
    return _request("GET", f"/api/users/{user_id}")


def admin_criar_usuario(payload: dict[str, Any]) -> dict[str, Any]:
    """Cria usuario administrativo."""
    return _request("POST", "/api/users", json=payload)


def admin_atualizar_usuario(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Atualiza usuario administrativo."""
    return _request("PUT", f"/api/users/{user_id}", json=payload)


def admin_alterar_senha_usuario(user_id: int, senha: str) -> dict[str, Any]:
    """Altera senha de usuario administrativo."""
    return _request("PATCH", f"/api/users/{user_id}/password", json={"senha": senha})


def admin_excluir_usuario(user_id: int) -> dict[str, Any]:
    """Exclui logicamente usuario administrativo."""
    return _request("DELETE", f"/api/users/{user_id}")


def obter_diagnostico_importacao(import_batch_id: int) -> dict[str, Any]:
    """Retorna diagnostico de uma importacao."""
    return _request("GET", f"/api/diagnostico/importacoes/{import_batch_id}")


def obter_diagnostico_campos(competencia: str) -> dict[str, Any]:
    """Retorna diagnostico de preenchimento dos campos financeiros."""
    return _request(
        "GET",
        "/api/diagnostico/campos",
        params={"competencia": competencia},
    )


def get_comparativo_mensal(
    competencia_base: str,
    competencia_comparacao: str,
) -> dict[str, Any]:
    """Retorna comparativo mensal entre duas competencias."""
    return _request(
        "GET",
        "/api/comparativo/mensal",
        params={
            "competencia_base": competencia_base,
            "competencia_comparacao": competencia_comparacao,
        },
    )


def get_relatorio_fornecedores(
    competencia: str,
    fornecedor: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retorna relatorio de gastos por fornecedor."""
    params: dict[str, Any] = {"competencia": competencia, "limit": limit}
    if fornecedor:
        params["fornecedor"] = fornecedor
    return _request("GET", "/api/relatorios/fornecedores", params=params)


def get_relatorio_servicos(
    competencia: str,
    servico: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retorna relatorio de gastos por servico."""
    params: dict[str, Any] = {"competencia": competencia, "limit": limit}
    if servico:
        params["servico"] = servico
    return _request("GET", "/api/relatorios/servicos", params=params)


def _request(method: str, path: str, authenticated: bool = True, **kwargs: Any) -> Any:
    """Executa requisicao HTTP e normaliza erros."""
    headers = dict(kwargs.pop("headers", {}) or {})
    if authenticated:
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            timeout=TIMEOUT,
            headers=headers,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as error:
        detail = _extract_error(response)
        if response.status_code == 401:
            _clear_auth_session()
            raise APIUnauthorizedError(
                detail or "Sessão expirada. Faça login novamente.",
            ) from error
        if response.status_code == 403:
            raise APIClientError(detail or "Acesso negado para esta operação.") from error
        raise APIClientError(detail) from error
    except requests.RequestException as error:
        raise APIClientError(f"Erro ao comunicar com a API: {error}") from error


def _extract_error(response: requests.Response) -> str:
    """Extrai mensagem legivel de erro da API."""
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Erro inesperado na API."

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    return str(detail or "Erro inesperado na API.")


def _clear_auth_session() -> None:
    """Remove dados locais de autenticacao."""
    for key in ("access_token", "token_type", "user", "roles", "permissions"):
        st.session_state.pop(key, None)
