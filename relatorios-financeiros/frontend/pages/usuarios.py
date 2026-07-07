"""Painel administrativo de usuarios."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from components.permissions import can, require_frontend_permission
from components.ui import (
    action_buttons,
    alert_box,
    error_box,
    info_box,
    page_footer,
    page_title,
    primary_button,
    render_metric_cards,
    render_table,
    section_title,
    success_box,
)
from components.users import avatar_initials, role_badges, user_actions, user_form, password_form
from services.api_client import (
    APIClientError,
    admin_alterar_senha_usuario,
    admin_atualizar_usuario,
    admin_criar_usuario,
    admin_excluir_usuario,
    admin_listar_usuarios,
)

ROLE_OPTIONS = ["Todos", "ADMIN", "FINANCEIRO", "CONSULTA"]
STATUS_OPTIONS = {"Todos": None, "Ativos": True, "Inativos": False}


def main() -> None:
    """Renderiza gestao administrativa de usuarios."""
    page_title("Usuários", "Gerenciamento de acessos ao sistema.")
    if not require_frontend_permission("usuarios.view"):
        page_footer()
        return

    filters = _render_filters()
    try:
        with st.spinner("Carregando usuários..."):
            response = admin_listar_usuarios(filters)
    except APIClientError as error:
        error_box(f"Não foi possível carregar usuários: {error}")
        page_footer()
        return

    users = response.get("items") or []
    _render_metrics(response, users)
    _render_create_action()
    _render_users_table(users)
    _render_selected_user_actions(users)
    _render_pagination(response)
    page_footer("Administração CETEL | Usuários")


def _render_filters() -> dict[str, Any]:
    """Renderiza filtros instantaneos."""
    with st.container(border=True):
        section_title("Filtros", "Pesquise usuários por dados cadastrais, papel e status.")
        col_name, col_email, col_role, col_status = st.columns(4, gap="large")
        nome = col_name.text_input("Nome", key="users_filter_name")
        email = col_email.text_input("Email", key="users_filter_email")
        papel = col_role.selectbox("Papel", options=ROLE_OPTIONS, key="users_filter_role")
        status_label = col_status.selectbox(
            "Status",
            options=list(STATUS_OPTIONS.keys()),
            key="users_filter_status",
        )
        refresh_clicked, clear_clicked = action_buttons(
            primary_key="users_refresh_button",
            secondary_key="users_clear_button",
        )
        if refresh_clicked:
            st.rerun()
        if clear_clicked:
            for key in (
                "users_filter_name",
                "users_filter_email",
                "users_filter_role",
                "users_filter_status",
                "users_page",
            ):
                st.session_state.pop(key, None)
            st.rerun()

    return {
        "nome": nome,
        "email": email,
        "papel": papel,
        "ativo": STATUS_OPTIONS[status_label],
        "page": st.session_state.get("users_page", 1),
        "page_size": st.session_state.get("users_page_size", 20),
        "order_by": st.session_state.get("users_order_by", "created_at"),
    }


def _render_metrics(response: dict[str, Any], users: list[dict[str, Any]]) -> None:
    """Renderiza cards administrativos."""
    total = int(response.get("total") or 0)
    active = sum(1 for user in users if user.get("ativo"))
    admins = sum(
        1
        for user in users
        if any(role.get("name") == "ADMIN" for role in user.get("papeis", []))
    )
    latest = _latest_created(users)
    render_metric_cards(
        [
            {"label": "Total usuários", "value": total, "icon": "U", "description": "Registros encontrados"},
            {"label": "Usuários ativos", "value": active, "icon": "✓", "description": "Nesta página"},
            {"label": "Administradores", "value": admins, "icon": "A", "description": "Nesta página"},
            {"label": "Último cadastro", "value": latest, "icon": "+", "description": "Mais recente na página"},
        ],
        columns=4,
    )


def _render_create_action() -> None:
    """Renderiza botao de novo usuario."""
    if not can("usuarios.create"):
        return
    col_action, _ = st.columns([1, 4], gap="large")
    with col_action:
        if primary_button("Novo usuário", key="new_user_button", icon="+"):
            _create_user_dialog()


def _render_users_table(users: list[dict[str, Any]]) -> None:
    """Renderiza tabela padronizada de usuarios."""
    section_title("Tabela", "Selecione um usuário abaixo para executar ações.")
    if not users:
        info_box("Nenhum usuário encontrado para os filtros selecionados.")
        return

    current_user = st.session_state.get("user") or {}
    options = {
        f"{user['nome']} - {user['email']}": int(user["id"])
        for user in users
    }
    selected_label = st.selectbox(
        "Usuário selecionado",
        options=list(options.keys()),
        key="selected_admin_user_label",
        help="Selecione o usuário para executar ações.",
    )
    st.session_state["selected_admin_user_id"] = options[selected_label]

    rows = []
    for user in users:
        role_names = ", ".join(role["name"] for role in user.get("papeis", []))
        actions = _actions_text()
        rows.append(
            {
                "ID": user["id"],
                "Avatar": avatar_initials(user.get("nome") or ""),
                "Nome": _current_user_label(user, current_user),
                "Email": user.get("email"),
                "Papéis": role_names,
                "Status": "Ativo" if user.get("ativo") else "Inativo",
                "Criado em": _format_datetime(user.get("created_at")),
                "Último acesso": _format_datetime(user.get("last_login_at")) or "-",
                "Ações": actions,
            },
        )
    frame = pd.DataFrame(rows)
    render_table(
        frame,
        height=360,
        caption="A coluna Ações indica operações disponíveis conforme suas permissões.",
    )


def _render_selected_user_actions(users: list[dict[str, Any]]) -> None:
    """Renderiza acoes do usuario selecionado."""
    selected_id = st.session_state.get("selected_admin_user_id")
    selected_user = next((user for user in users if user["id"] == selected_id), None)
    if selected_user is None:
        info_box("Selecione um usuário na tabela para editar, alterar senha, ativar, desativar ou excluir.")
        return

    with st.container(border=True):
        section_title("Ações", "Operações aplicadas ao usuário selecionado.")
        st.markdown(
            (
                f"**{selected_user['nome']}**  \n"
                f"{selected_user['email']}  \n"
                f"{role_badges(selected_user.get('papeis', []))}"
            ),
            unsafe_allow_html=True,
        )
        action = user_actions(selected_user, f"user_{selected_user['id']}")
        if action == "edit":
            _edit_user_dialog(selected_user)
        elif action == "password":
            _password_dialog(selected_user)
        elif action == "toggle":
            _toggle_user_dialog(selected_user)
        elif action == "delete":
            _delete_user_dialog(selected_user)


def _render_pagination(response: dict[str, Any]) -> None:
    """Renderiza paginacao e ordenacao."""
    total = int(response.get("total") or 0)
    page_size = int(response.get("page_size") or 20)
    total_pages = max((total + page_size - 1) // page_size, 1)
    with st.container(border=True):
        section_title("Paginação", "Controle a quantidade e a ordenação dos registros.")
        col_page, col_size, col_order = st.columns(3, gap="large")
        page = col_page.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=min(int(response.get("page") or 1), total_pages),
            step=1,
            key="users_page_input",
        )
        size = col_size.selectbox(
            "Itens por página",
            options=[10, 20, 50, 100],
            index=[10, 20, 50, 100].index(page_size if page_size in {10, 20, 50, 100} else 20),
            key="users_page_size_input",
        )
        order_by = col_order.selectbox(
            "Ordenar por",
            options=["created_at", "nome", "email"],
            format_func={"created_at": "Criado em", "nome": "Nome", "email": "Email"}.get,
            key="users_order_by_input",
        )
        if (
            st.session_state.get("users_page") != int(page)
            or st.session_state.get("users_page_size") != int(size)
            or st.session_state.get("users_order_by") != order_by
        ):
            st.session_state["users_page"] = int(page)
            st.session_state["users_page_size"] = int(size)
            st.session_state["users_order_by"] = order_by


@st.dialog("Novo usuário")
def _create_user_dialog() -> None:
    payload, submitted = user_form("create_user", include_password=True)
    if submitted and _validate_user_payload(payload, include_password=True):
        try:
            admin_criar_usuario(_api_payload(payload, include_password=True))
            st.toast("Usuário criado com sucesso.", icon="✓")
            st.rerun()
        except APIClientError as error:
            st.toast(str(error), icon="!")
            error_box(str(error))


@st.dialog("Editar usuário")
def _edit_user_dialog(user: dict[str, Any]) -> None:
    payload, submitted = user_form(f"edit_user_{user['id']}", user=user)
    if submitted and _validate_user_payload(payload):
        try:
            admin_atualizar_usuario(user["id"], _api_payload(payload))
            st.toast("Usuário atualizado com sucesso.", icon="✓")
            st.rerun()
        except APIClientError as error:
            st.toast(str(error), icon="!")
            error_box(str(error))


@st.dialog("Alterar senha")
def _password_dialog(user: dict[str, Any]) -> None:
    senha, confirmar, submitted = password_form(f"password_user_{user['id']}")
    if submitted:
        if len(senha) < 8:
            error_box("A senha deve ter pelo menos 8 caracteres.")
            return
        if senha != confirmar:
            error_box("A confirmação de senha não confere.")
            return
        try:
            admin_alterar_senha_usuario(user["id"], senha)
            st.toast("Senha alterada com sucesso.", icon="✓")
            st.rerun()
        except APIClientError as error:
            st.toast(str(error), icon="!")
            error_box(str(error))


@st.dialog("Confirmar alteração de status")
def _toggle_user_dialog(user: dict[str, Any]) -> None:
    next_status = not bool(user.get("ativo"))
    action = "ativar" if next_status else "desativar"
    alert_box(f"Confirme para {action} o usuário {user['email']}.", status="warning")
    if st.checkbox(f"Confirmo que desejo {action} este usuário.", key=f"confirm_toggle_{user['id']}"):
        if primary_button(action, key=f"confirm_toggle_button_{user['id']}"):
            payload = {
                "nome": user["nome"],
                "email": user["email"],
                "ativo": next_status,
                "papeis": [role["name"] for role in user.get("papeis", [])],
            }
            try:
                admin_atualizar_usuario(user["id"], payload)
                st.toast("Status atualizado com sucesso.", icon="✓")
                st.rerun()
            except APIClientError as error:
                st.toast(str(error), icon="!")
                error_box(str(error))


@st.dialog("Confirmar exclusão")
def _delete_user_dialog(user: dict[str, Any]) -> None:
    alert_box(
        f"Esta ação desativa o usuário {user['email']} sem apagar registros.",
        status="warning",
    )
    if st.checkbox("Confirmo que desejo excluir logicamente este usuário.", key=f"confirm_delete_{user['id']}"):
        if primary_button("Excluir", key=f"confirm_delete_button_{user['id']}"):
            try:
                admin_excluir_usuario(user["id"])
                st.toast("Usuário excluído com sucesso.", icon="✓")
                st.rerun()
            except APIClientError as error:
                st.toast(str(error), icon="!")
                error_box(str(error))


def _validate_user_payload(payload: dict[str, Any], include_password: bool = False) -> bool:
    """Valida formulario antes de enviar."""
    if not payload["nome"] or len(payload["nome"]) < 2:
        error_box("Informe um nome válido.")
        return False
    if "@" not in payload["email"]:
        error_box("Informe um email válido.")
        return False
    if not payload["papeis"]:
        error_box("Selecione pelo menos um papel.")
        return False
    if include_password:
        if len(payload.get("senha") or "") < 8:
            error_box("A senha deve ter pelo menos 8 caracteres.")
            return False
        if payload.get("senha") != payload.get("confirmar_senha"):
            error_box("A confirmação de senha não confere.")
            return False
    return True


def _api_payload(payload: dict[str, Any], include_password: bool = False) -> dict[str, Any]:
    data = {
        "nome": payload["nome"],
        "email": payload["email"],
        "ativo": payload["ativo"],
        "papeis": payload["papeis"],
    }
    if include_password:
        data["senha"] = payload["senha"]
    return data


def _actions_text() -> str:
    actions = []
    if can("usuarios.update"):
        actions.extend(["Editar", "Senha", "Ativar/Desativar"])
    if can("usuarios.delete"):
        actions.append("Excluir")
    return ", ".join(actions) or "Sem ações"


def _current_user_label(user: dict[str, Any], current_user: dict[str, Any]) -> str:
    suffix = " (você)" if int(user["id"]) == int(current_user.get("id") or 0) else ""
    return f"{user.get('nome')}{suffix}"


def _latest_created(users: list[dict[str, Any]]) -> str:
    dates = [user.get("created_at") for user in users if user.get("created_at")]
    if not dates:
        return "-"
    return _format_datetime(max(dates)) or "-"


def _format_datetime(value: object) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.strftime("%d/%m/%Y %H:%M")


if __name__ == "__main__":
    main()
