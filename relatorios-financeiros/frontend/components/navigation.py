"""Compatibilidade para identidade visual da navegacao."""

from __future__ import annotations

import streamlit as st

from components.ui import app_header, apply_global_styles


def render_sidebar(active_page: str | None = None) -> None:
    """Aplica estilos e exibe uma marca discreta quando chamado por codigo legado."""
    apply_global_styles()
    with st.sidebar:
        app_header(st.session_state.get("user"))
