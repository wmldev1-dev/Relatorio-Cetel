"""Componentes reutilizaveis da gestao de usuarios."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from components.permissions import can
from components.ui import password_input, secondary_button

AVAILABLE_ROLES = ("ADMIN", "FINANCEIRO", "CONSULTA")


def avatar_initials(name: str) -> str:
    """Retorna iniciais para avatar."""
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "U"
    return "".join(part[0].upper() for part in parts[:2])


def status_badge(active: bool) -> str:
    """HTML de status do usuario."""
    css = "success" if active else "danger"
    text = "ATIVO" if active else "INATIVO"
    return f'<span class="rf-status-badge rf-status-{css}">{text}</span>'


def role_badges(roles: list[dict[str, Any]] | list[str]) -> str:
    """HTML de badges de papeis."""
    names = [
        str(role.get("name")) if isinstance(role, dict) else str(role)
        for role in roles
    ]
    colors = {
        "ADMIN": "danger",
        "FINANCEIRO": "success",
        "CONSULTA": "neutral",
    }
    return " ".join(
        f'<span class="rf-status-badge rf-status-{colors.get(name, "neutral")}">{escape(name)}</span>'
        for name in names
    )


def user_form(
    key_prefix: str,
    user: dict[str, Any] | None = None,
    include_password: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Renderiza formulario de usuario."""
    current_roles = [
        role["name"]
        for role in (user or {}).get("papeis", [])
        if role.get("name") in AVAILABLE_ROLES
    ]
    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        nome = st.text_input("Nome", value=str((user or {}).get("nome") or ""), key=f"{key_prefix}_nome")
        email = st.text_input("Email", value=str((user or {}).get("email") or ""), key=f"{key_prefix}_email")
        senha = ""
        confirmar = ""
        if include_password:
            senha = password_input("Senha", key=f"{key_prefix}_senha")
            confirmar = password_input("Confirmar senha", key=f"{key_prefix}_confirmar")
        papeis = st.multiselect(
            "Papéis",
            options=list(AVAILABLE_ROLES),
            default=current_roles or ["CONSULTA"],
            key=f"{key_prefix}_papeis",
        )
        ativo = st.toggle(
            "Ativo",
            value=bool((user or {}).get("ativo", True)),
            key=f"{key_prefix}_ativo",
        )
        submitted = st.form_submit_button("SALVAR", type="primary", width="stretch")
    payload: dict[str, Any] = {
        "nome": nome.strip(),
        "email": email.strip().lower(),
        "ativo": ativo,
        "papeis": papeis,
    }
    if include_password:
        payload["senha"] = senha
        payload["confirmar_senha"] = confirmar
    return payload, submitted


def password_form(key_prefix: str) -> tuple[str, str, bool]:
    """Renderiza formulario de senha."""
    with st.form(f"{key_prefix}_password_form", clear_on_submit=False):
        senha = password_input("Nova senha", key=f"{key_prefix}_senha")
        confirmar = password_input("Confirmar senha", key=f"{key_prefix}_confirmar")
        submitted = st.form_submit_button("ALTERAR SENHA", type="primary", width="stretch")
    return senha, confirmar, submitted


def user_actions(user: dict[str, Any], key_prefix: str) -> str | None:
    """Renderiza acoes disponiveis para um usuario selecionado."""
    action = None
    cols = st.columns(4, gap="medium")
    with cols[0]:
        if can("usuarios.update") and secondary_button("Editar", key=f"{key_prefix}_edit"):
            action = "edit"
    with cols[1]:
        if can("usuarios.update") and secondary_button("Senha", key=f"{key_prefix}_password"):
            action = "password"
    with cols[2]:
        label = "Desativar" if user.get("ativo") else "Ativar"
        if can("usuarios.update") and secondary_button(label, key=f"{key_prefix}_toggle"):
            action = "toggle"
    with cols[3]:
        if can("usuarios.delete") and secondary_button("Excluir", key=f"{key_prefix}_delete"):
            action = "delete"
    return action
