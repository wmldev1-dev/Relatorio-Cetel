"""Helpers de autorizacao no frontend."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from components.ui import alert_box


def can(permission: str) -> bool:
    """Verifica uma permissao cacheada na sessao."""
    return permission in set(st.session_state.get("permissions") or [])


def can_any(*permissions: str) -> bool:
    """Verifica se alguma permissao esta disponivel."""
    return any(can(permission) for permission in permissions)


def can_all(*permissions: str) -> bool:
    """Verifica se todas as permissoes estao disponiveis."""
    return all(can(permission) for permission in permissions)


def can_module(module: str) -> bool:
    """Verifica acesso de visualizacao ao modulo."""
    return can(f"{module}.view")


def protected_component(permission: str, render: Callable[[], None]) -> None:
    """Renderiza componente somente quando autorizado."""
    if can(permission):
        render()


def require_frontend_permission(permission: str) -> bool:
    """Mostra mensagem amigavel quando uma pagina nao esta autorizada."""
    if can(permission):
        return True
    alert_box("Você não possui permissão para acessar esta área.", status="warning")
    return False
