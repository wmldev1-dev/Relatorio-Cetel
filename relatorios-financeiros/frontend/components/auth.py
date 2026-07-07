"""Componentes e guardas de autenticacao do Streamlit."""

from __future__ import annotations

import streamlit as st

from components.ui import alert_box, app_header, login_card, secondary_button
from services.api_client import (
    APIClientError,
    APIUnauthorizedError,
    get_auth_permissions,
    get_me,
    login,
    logout,
)


def is_authenticated() -> bool:
    """Indica se ha token e usuario na sessao."""
    return bool(st.session_state.get("access_token") and st.session_state.get("user"))


def render_login_page() -> None:
    """Renderiza login e salva token no session_state."""
    error_message = st.session_state.pop("login_error", None)
    email, password, submitted = login_card(error_message)
    if not submitted:
        return

    if not email or not password:
        st.session_state["login_error"] = "Informe email e senha para entrar."
        st.rerun()

    try:
        result = login(email.strip(), password)
    except APIUnauthorizedError:
        st.session_state["login_error"] = "Email ou senha inválidos."
        st.rerun()
    except APIClientError as error:
        st.session_state["login_error"] = f"Não foi possível entrar: {error}"
        st.rerun()

    st.session_state["access_token"] = result["access_token"]
    st.session_state["token_type"] = result.get("token_type", "bearer")
    st.session_state["user"] = result["user"]
    _load_permissions()
    st.rerun()


def ensure_authenticated() -> bool:
    """Valida a sessao atual e exibe login quando necessario."""
    if not st.session_state.get("access_token"):
        render_login_page()
        return False

    if not st.session_state.get("user"):
        try:
            st.session_state["user"] = get_me()
        except APIClientError:
            clear_auth_session()
            render_login_page()
            return False
    if not st.session_state.get("permissions"):
        try:
            _load_permissions()
        except APIClientError:
            clear_auth_session()
            render_login_page()
            return False
    return True


def render_authenticated_sidebar() -> None:
    """Renderiza marca, usuario e botao de saida."""
    with st.sidebar:
        app_header(st.session_state.get("user"))
        if secondary_button("Sair", key="logout_button", icon="×"):
            try:
                logout()
            except APIClientError:
                pass
            clear_auth_session()
            st.rerun()


def clear_auth_session() -> None:
    """Limpa os dados locais da sessao autenticada."""
    for key in ("access_token", "token_type", "user", "roles", "permissions", "login_error"):
        st.session_state.pop(key, None)


def handle_auth_error(error: APIClientError) -> None:
    """Exibe mensagem amigavel para falhas de autenticacao."""
    if isinstance(error, APIUnauthorizedError):
        clear_auth_session()
        alert_box("Sessão expirada. Faça login novamente.", status="warning")
        st.rerun()
    raise error


def _load_permissions() -> None:
    """Carrega papeis e permissoes do usuario autenticado."""
    payload = get_auth_permissions()
    st.session_state["roles"] = payload.get("roles") or []
    st.session_state["permissions"] = [
        item["code"]
        for item in payload.get("permissions") or []
        if item.get("code")
    ]
