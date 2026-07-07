"""Componentes visuais reutilizaveis do frontend Streamlit."""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from typing import Iterator

import pandas as pd
import streamlit as st

from utils.table_formatters import build_column_config, prepare_dataframe_for_display, shape_table


def apply_global_styles() -> None:
    """Aplica a identidade visual light da aplicacao."""
    st.markdown(
        """
        <style>
            :root {
                --rf-primary: #2563EB;
                --rf-primary-dark: #1D4ED8;
                --rf-primary-soft: #DBEAFE;
                --rf-cyan: #06B6D4;
                --rf-success: #16A34A;
                --rf-danger: #DC2626;
                --rf-warning: #F59E0B;
                --rf-bg: #F8FAFC;
                --rf-card: #FFFFFF;
                --rf-border: #E2E8F0;
                --rf-text: #0F172A;
                --rf-muted: #64748B;
                --rf-shadow: rgba(15, 23, 42, 0.07);
                --rf-radius: 16px;
            }
            .stApp,
            div[data-testid="stAppViewContainer"],
            div[data-testid="stAppViewContainer"] > .main {
                background: var(--rf-bg) !important;
                color: var(--rf-text) !important;
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            header[data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0.96) !important;
                border-bottom: 1px solid var(--rf-border) !important;
                box-shadow: none !important;
            }
            div[data-testid="stDecoration"] {
                display: none !important;
            }
            .block-container {
                max-width: 1440px;
                padding-top: 3rem;
                padding-bottom: 2.25rem;
            }
            div[data-testid="stVerticalBlock"] {
                gap: 0.8rem;
            }
            div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
                gap: 0.75rem;
            }
            [data-testid="stSidebar"] {
                background: var(--rf-card) !important;
                border-right: 1px solid var(--rf-border);
            }
            [data-testid="stSidebarNav"] {
                padding-top: 0.7rem;
            }
            [data-testid="stSidebarNav"] ul {
                gap: 0.25rem;
            }
            [data-testid="stSidebarNav"] a {
                border-radius: 12px;
                color: var(--rf-text) !important;
                font-weight: 650;
                margin: 0.08rem 0.4rem;
                padding: 0.55rem 0.7rem;
            }
            [data-testid="stSidebarNav"] a:hover {
                background: #EFF6FF;
            }
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: var(--rf-primary-soft);
                color: var(--rf-primary-dark) !important;
            }
            .rf-page-header {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: 18px;
                box-shadow: 0 10px 28px var(--rf-shadow);
                margin-bottom: 1rem;
                padding: 1.1rem 1.25rem;
            }
            .rf-page-header-top {
                align-items: center;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
            }
            .rf-page-title {
                color: var(--rf-text);
                font-size: clamp(1.35rem, 2vw, 1.85rem);
                font-weight: 800;
                letter-spacing: 0.018em;
                line-height: 1.15;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-page-subtitle {
                color: var(--rf-muted);
                font-size: 0.94rem;
                line-height: 1.45;
                margin: 0.35rem 0 0;
                max-width: 780px;
            }
            .rf-badge,
            .rf-status-badge {
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.025em;
                line-height: 1;
                padding: 0.42rem 0.62rem;
                text-transform: uppercase;
            }
            .rf-status-neutral { background: #F1F5F9; color: #334155; }
            .rf-status-success { background: #DCFCE7; color: #166534; }
            .rf-status-warning { background: #FEF3C7; color: #92400E; }
            .rf-status-danger { background: #FEE2E2; color: #991B1B; }
            .rf-section-head {
                margin: 1.15rem 0 0.55rem;
            }
            .rf-section-title {
                color: var(--rf-text);
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-section-description,
            .rf-muted {
                color: var(--rf-muted);
                font-size: 0.88rem;
                line-height: 1.45;
                margin: 0.25rem 0 0;
            }
            .rf-filter-panel,
            div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stForm"] {
                background: var(--rf-card) !important;
                border: 1px solid var(--rf-border) !important;
                border-radius: var(--rf-radius) !important;
                box-shadow: 0 8px 22px var(--rf-shadow);
            }
            .rf-filter-panel {
                border-left: 4px solid var(--rf-primary) !important;
                margin: 0.1rem 0 0.65rem;
                padding: 0.95rem 1rem;
            }
            .rf-dashboard-block {
                margin-top: 0.35rem;
            }
            .rf-metric-grid,
            .rf-card-grid,
            .rf-card-row {
                align-items: stretch;
                box-sizing: border-box;
                display: grid;
                gap: 20px;
                margin-bottom: 24px;
                overflow: hidden;
                width: 100%;
            }
            .rf-metric-grid {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
            .rf-card-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .rf-card-row {
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            }
            .rf-card,
            .rf-section-card,
            .rf-chart-card,
            .rf-table-card {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: var(--rf-radius);
                box-sizing: border-box;
                box-shadow: 0 8px 22px var(--rf-shadow);
                margin-bottom: 24px;
                overflow: hidden;
                width: 100%;
            }
            .rf-card,
            .rf-section-card {
                height: 100%;
                padding: 20px;
            }
            .rf-chart-card {
                padding: 0.25rem 0.35rem 0;
            }
            .rf-table-card {
                margin-top: 4px;
            }
            .rf-grid {
                display: grid;
                gap: 20px;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                margin-bottom: 24px;
            }
            @media (max-width: 1180px) {
                .rf-grid,
                .rf-metric-grid,
                .rf-card-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }
            @media (max-width: 760px) {
                .rf-grid,
                .rf-metric-grid,
                .rf-card-grid {
                    grid-template-columns: 1fr;
                }
                .block-container {
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                }
            }
            .rf-filter-title {
                color: var(--rf-text);
                font-size: 0.82rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-filter-description {
                color: var(--rf-muted);
                font-size: 0.8rem;
                margin: 0.25rem 0 0;
            }
            label,
            div[data-testid="stSelectbox"] label,
            div[data-testid="stDateInput"] label,
            div[data-testid="stNumberInput"] label,
            div[data-testid="stTextInput"] label,
            div[data-testid="stFileUploader"] label {
                color: var(--rf-text) !important;
                font-size: 0.74rem !important;
                font-weight: 760 !important;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            input,
            textarea,
            div[data-testid="stFileUploader"] section {
                background: #FFFFFF !important;
                border: 1.5px solid #CBD5E1 !important;
                border-radius: 12px !important;
                color: var(--rf-text) !important;
            }
            div[data-baseweb="select"] > div:focus-within,
            div[data-baseweb="input"] > div:focus-within {
                border-color: var(--rf-primary) !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
            }
            .stButton > button {
                border-radius: 12px !important;
                font-weight: 760 !important;
                letter-spacing: 0.025em;
                min-height: 2.65rem;
                min-width: 10.5rem;
                text-transform: uppercase;
            }
            div[data-testid="stFormSubmitButton"] > button {
                border-radius: 12px !important;
                font-weight: 760 !important;
                letter-spacing: 0.025em;
                min-height: 2.65rem;
                min-width: 10.5rem;
                text-transform: uppercase;
            }
            .rf-button-row {
                margin-top: 0.65rem;
            }
            .rf-metric-card {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-left: 4px solid var(--rf-primary);
                border-radius: var(--rf-radius);
                box-sizing: border-box;
                box-shadow: 0 8px 22px var(--rf-shadow);
                display: flex;
                flex-direction: column;
                height: 100%;
                justify-content: space-between;
                margin-bottom: 20px;
                min-height: 156px;
                overflow: hidden;
                padding: 20px;
                width: 100%;
            }
            .rf-metric-row-spacer {
                height: 20px;
                width: 100%;
            }
            .rf-metric-card.rf-status-success { border-left-color: var(--rf-success); }
            .rf-metric-card.rf-status-warning { border-left-color: var(--rf-warning); }
            .rf-metric-card.rf-status-danger { border-left-color: var(--rf-danger); }
            .rf-metric-card.rf-metric-long .rf-metric-value {
                display: -webkit-box;
                font-size: 0.95rem;
                line-height: 1.28;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                min-height: 3.65rem;
                overflow: hidden;
            }
            .rf-metric-top {
                align-items: flex-start;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
                min-height: 2.35rem;
            }
            .rf-metric-label {
                color: var(--rf-muted);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                line-height: 1.2;
                margin: 0;
                max-width: calc(100% - 3rem);
                text-transform: uppercase;
                word-break: normal;
            }
            .rf-metric-icon {
                align-items: center;
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                color: var(--rf-primary-dark);
                display: inline-flex;
                flex: 0 0 2.25rem;
                font-size: 0.95rem;
                font-weight: 800;
                height: 2.25rem;
                justify-content: center;
                width: 2.25rem;
            }
            .rf-metric-value {
                color: var(--rf-text);
                font-size: clamp(1.08rem, 1.7vw, 1.48rem);
                font-weight: 800;
                line-height: 1.18;
                margin: 0.65rem 0 0;
                min-height: 2.1rem;
                overflow-wrap: anywhere;
                word-break: break-word;
                white-space: normal;
            }
            .rf-metric-description {
                color: var(--rf-muted);
                font-size: 0.78rem;
                line-height: 1.32;
                margin: 0.45rem 0 0.75rem;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .rf-metric-trend {
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.035em;
                line-height: 1;
                margin-top: 0.75rem;
                padding: 0.4rem 0.55rem;
                text-transform: uppercase;
                width: fit-content;
            }
            .rf-metric-card.rf-status-success .rf-metric-trend {
                background: #DCFCE7;
                color: #166534;
            }
            .rf-metric-card.rf-status-warning .rf-metric-trend {
                background: #FEF3C7;
                color: #92400E;
            }
            .rf-metric-card.rf-status-danger .rf-metric-trend {
                background: #FEE2E2;
                color: #991B1B;
            }
            .rf-metric-card.rf-status-neutral .rf-metric-trend,
            .rf-metric-trend {
                background: #F1F5F9;
                color: #334155;
            }
            .rf-empty-state {
                background: var(--rf-card);
                border: 1px dashed #CBD5E1;
                border-radius: var(--rf-radius);
                color: var(--rf-muted);
                padding: 1.25rem;
                text-align: center;
            }
            .rf-empty-title {
                color: var(--rf-text);
                font-weight: 800;
                margin: 0 0 0.25rem;
                text-transform: uppercase;
            }
            div[data-testid="stDataFrame"] {
                background: #FFFFFF !important;
                border: 1px solid var(--rf-border) !important;
                border-radius: var(--rf-radius) !important;
                color: var(--rf-text) !important;
            }
            div[data-testid="stDataFrame"] [role="columnheader"] {
                background: #EAF2FF !important;
                color: var(--rf-text) !important;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.045em;
                text-transform: uppercase;
            }
            .rf-table-title {
                color: var(--rf-text);
                font-size: 0.9rem;
                font-weight: 800;
                letter-spacing: 0.045em;
                margin: 0 0 0.55rem;
                text-transform: uppercase;
            }
            .rf-table-caption {
                color: var(--rf-muted);
                font-size: 0.78rem;
                margin: -0.1rem 0 0.55rem;
            }
            .rf-footer {
                border-top: 1px solid var(--rf-border);
                color: var(--rf-muted);
                font-size: 0.78rem;
                margin-top: 2rem;
                padding-top: 1rem;
                text-align: right;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None, badge: str | None = None) -> None:
    """Renderiza cabecalho de pagina."""
    badge_markup = status_badge(badge, "neutral", render=False) if badge else ""
    subtitle_markup = f'<p class="rf-page-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        (
            '<div class="rf-page-header">'
            '<div class="rf-page-header-top">'
            f'<h1 class="rf-page-title">{escape(title.upper())}</h1>'
            f"{badge_markup}"
            "</div>"
            f"{subtitle_markup}"
            "</div>"
        ),
    )


@contextmanager
def section_card(title: str | None = None, description: str | None = None) -> Iterator[None]:
    """Container visual para secoes."""
    if title:
        section_title(title, description)
    st.markdown('<div class="rf-section-card">', unsafe_allow_html=True)
    with st.container(border=True):
        yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def section_container(title: str | None = None, description: str | None = None) -> Iterator[None]:
    """Container padronizado para blocos de conteudo."""
    if title:
        section_title(title, description)
    st.markdown('<div class="rf-section-card">', unsafe_allow_html=True)
    with st.container(border=True):
        yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def filter_panel(title: str = "FILTROS", description: str | None = None) -> Iterator[None]:
    """Container visual para filtros."""
    description_markup = f'<p class="rf-filter-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f"""
        <div class="rf-filter-panel">
            <p class="rf-filter-title">{escape(title.upper())}</p>
            {description_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        yield


def metric_grid(columns: int = 4) -> list[object]:
    """Cria grade padronizada para cards de metricas."""
    return list(st.columns(columns, gap="large"))


def card_grid(columns: int = 2) -> list[object]:
    """Cria grade padronizada para cards e graficos menores."""
    return list(st.columns(columns, gap="large"))


def render_metric_cards(cards: list[dict[str, object]], columns: int = 4) -> None:
    """Renderiza cards de metrica com grade e espaçamento padronizados."""
    st.markdown('<div class="rf-metric-grid">', unsafe_allow_html=True)
    chunks = list(range(0, len(cards), columns))
    for chunk_index, chunk_start in enumerate(chunks):
        row = cards[chunk_start:chunk_start + columns]
        cols = metric_grid(columns)
        for column, card in zip(cols, row, strict=False):
            with column:
                metric_card(
                    str(card.get("label") or ""),
                    card.get("value", ""),
                    str(card.get("icon") or ""),
                    str(card.get("description") or ""),
                    status=str(card.get("status")) if card.get("status") else None,
                )
        if chunk_index < len(chunks) - 1:
            st.markdown('<div class="rf-metric-row-spacer"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def primary_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao primario padronizado."""
    return st.button(
        _button_label(label, icon),
        type="primary",
        key=key,
        width="stretch",
        disabled=disabled,
    )


def secondary_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao secundario padronizado."""
    return st.button(
        _button_label(label, icon),
        type="secondary",
        key=key,
        width="stretch",
        disabled=disabled,
    )


def danger_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao destrutivo padronizado."""
    return secondary_button(label, key=key, icon=icon or "!", disabled=disabled)


def action_buttons(
    primary_label: str = "ATUALIZAR",
    secondary_label: str = "LIMPAR FILTROS",
    primary_key: str | None = None,
    secondary_key: str | None = None,
) -> tuple[bool, bool]:
    """Renderiza botoes de filtro alinhados a direita."""
    st.markdown('<div class="rf-button-row">', unsafe_allow_html=True)
    _, _, primary_col, secondary_col = st.columns([2.2, 2.2, 1.15, 1.15], gap="medium")
    with primary_col:
        primary_clicked = primary_button(primary_label, key=primary_key, icon="↻")
    with secondary_col:
        secondary_clicked = secondary_button(secondary_label, key=secondary_key, icon="×")
    st.markdown("</div>", unsafe_allow_html=True)
    return primary_clicked, secondary_clicked


def metric_card(
    label: str,
    value: object,
    icon: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> None:
    """Renderiza card de indicador."""
    if description is not None and icon is not None and len(str(icon)) > 3 and len(str(description)) <= 3:
        icon, description = description, icon
    long_class = " rf-metric-long" if len(str(value)) > 48 else ""
    status_class = f" rf-status-{status}" if status else " rf-status-neutral"
    description_text, trend_text = _split_metric_description(description)
    description_markup = (
        f'<p class="rf-metric-description">{escape(description_text)}</p>'
        if description_text else ""
    )
    trend_markup = (
        f'<span class="rf-metric-trend">{escape(trend_text)}</span>'
        if trend_text else ""
    )
    icon_markup = f'<span class="rf-metric-icon">{escape(icon or "•")}</span>'
    st.markdown(
        f"""
        <div class="rf-metric-card{status_class}{long_class}">
            <div class="rf-metric-top">
                <p class="rf-metric-label">{escape(label.upper())}</p>
                {icon_markup}
            </div>
            <p class="rf-metric-value">{escape(str(value))}</p>
            {description_markup}
            {trend_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text: str, status: str = "neutral", render: bool = True) -> str | None:
    """Renderiza badge de status."""
    markup = f'<span class="rf-status-badge rf-status-{escape(status)}">{escape(text.upper())}</span>'
    if render:
        st.markdown(markup, unsafe_allow_html=True)
        return None
    return markup


def empty_state(title: str, message: str, icon: str | None = None) -> None:
    """Renderiza estado vazio amigavel."""
    icon_markup = f"<div>{escape(icon)}</div>" if icon else ""
    st.markdown(
        f"""
        <div class="rf-empty-state">
            {icon_markup}
            <p class="rf-empty-title">{escape(title)}</p>
            <p>{escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table(
    df: pd.DataFrame,
    title: str | None = None,
    height: int = 520,
    key: str | None = None,
    caption: str | None = None,
    column_order: list[str] | tuple[str, ...] | None = None,
    hidden_columns: list[str] | tuple[str, ...] | None = None,
) -> None:
    """Renderiza tabela padronizada com st.dataframe e column_config."""
    prepared_df = prepare_dataframe_for_display(
        shape_table(df, column_order, hidden_columns),
    )
    st.markdown('<div class="rf-table-card">', unsafe_allow_html=True)
    with st.container(border=True):
        if title:
            st.markdown(f'<p class="rf-table-title">{escape(title.upper())}</p>', unsafe_allow_html=True)
        if caption:
            st.markdown(f'<p class="rf-table-caption">{escape(caption)}</p>', unsafe_allow_html=True)
        if prepared_df.empty:
            empty_state("Sem registros", "Nenhum dado disponível para exibição.")
        else:
            st.dataframe(
                prepared_df,
                column_config=build_column_config(prepared_df),
                height=height,
                hide_index=True,
                key=key,
                width="stretch",
            )
    st.markdown("</div>", unsafe_allow_html=True)


def page_footer(text: str = "UI CETEL LIGHT BI v3") -> None:
    """Renderiza rodape padrao."""
    st.markdown(f'<div class="rf-footer">{escape(text)}</div>', unsafe_allow_html=True)


def section_title(title: str, description: str | None = None) -> None:
    """Renderiza titulo de secao."""
    description_markup = f'<p class="rf-section-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f"""
        <div class="rf-section-head">
            <h2 class="rf-section-title">{escape(title.upper())}</h2>
            {description_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(message: str) -> None:
    st.info(message)


def warning_box(message: str) -> None:
    st.warning(message)


def error_box(message: str) -> None:
    st.error(message)


def success_box(message: str) -> None:
    st.success(message)


def filter_header(title: str, description: str | None = None) -> None:
    """Compatibilidade com filtros no sidebar do dashboard."""
    description_markup = f'<p class="rf-filter-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f'<div class="rf-filter-panel"><p class="rf-filter-title">{escape(title.upper())}</p>{description_markup}</div>',
        unsafe_allow_html=True,
    )


def filter_group_title(title: str) -> None:
    st.markdown(f'<p class="rf-section-title">{escape(title.upper())}</p>', unsafe_allow_html=True)


# Compatibilidade com chamadas antigas.
page_title = page_header


def _html(markup: str) -> None:
    """Renderiza HTML sem deixar o parser Markdown expor tags como texto."""
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def _split_metric_description(description: str | None) -> tuple[str | None, str | None]:
    """Separa descricao e tendencia quando o texto usa o padrao 'descricao | tendencia'."""
    if not description:
        return None, None
    if "|" not in description:
        return description, None
    description_text, trend_text = description.rsplit("|", 1)
    return description_text.strip() or None, trend_text.strip() or None


def _button_label(label: str, icon: str | None = None) -> str:
    text = label.upper()
    return f"{icon} {text}" if icon else text
