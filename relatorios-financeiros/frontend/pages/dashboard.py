"""Dashboard executivo financeiro."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st

from components.charts import (
    executive_city_bar,
    executive_comparison_columns,
    executive_donut,
    executive_horizontal_bar,
    executive_monthly_line,
)
from components.ui import (
    action_buttons,
    card_grid,
    error_box,
    filter_group_title,
    info_box,
    page_footer,
    page_header,
    render_metric_cards,
    render_table,
    section_title,
    warning_box,
)
from services.api_client import APIClientError, listar_dashboard_executivo

MANAGEMENT_HIDDEN_COLUMNS = (
    "id",
    "competence_id",
    "import_batch_id",
    "id_importacao",
    "arquivo_salvo",
    "file_path",
    "caminho_arquivo",
    "created_at",
    "updated_at",
    "created_at_source",
)


def main() -> None:
    """Renderiza a tela principal executiva."""
    page_header(
        "Dashboard Executivo",
        "Visão financeira consolidada para leitura gerencial em até 30 segundos.",
        badge="EXECUTIVO",
    )

    try:
        with st.spinner("Carregando filtros e indicadores..."):
            initial_dashboard = _load_dashboard({})
        filters = _render_header_filters(initial_dashboard)
        with st.spinner("Atualizando dashboard executivo..."):
            dashboard = _load_dashboard(filters)
        _render_dashboard(dashboard)
        page_footer("Dashboard Executivo CETEL | Tema Light")
    except APIClientError as error:
        error_box(f"Não foi possível carregar o dashboard executivo: {error}")
        page_footer("Dashboard Executivo CETEL | Tema Light")


@st.cache_data(ttl=120, show_spinner=False)
def _load_dashboard(filters: dict[str, Any]) -> dict[str, Any]:
    """Carrega o dashboard executivo com cache curto."""
    return listar_dashboard_executivo(filters)


def _render_header_filters(initial_dashboard: dict[str, Any]) -> dict[str, Any]:
    """Renderiza competência, filtros globais e ações."""
    options = initial_dashboard.get("filters") or {}
    competences = [item["periodo"] for item in options.get("competencias") or []]
    selected_default = options.get("competencia_selecionada")
    default_index = competences.index(selected_default) if selected_default in competences else 0

    with st.container(border=True):
        section_title("Competência e filtros globais", "Todos os blocos respondem aos filtros abaixo.")
        filter_group_title("Filtros principais")
        col_competence, col_supplier, col_category, col_service = st.columns(4, gap="large")
        selected_competence = col_competence.selectbox(
            "Competência",
            options=competences,
            index=default_index,
            key="exec_competence",
            help="Competência principal do dashboard.",
        )
        selected_supplier = col_supplier.selectbox(
            "Fornecedor",
            options=["Todos"] + list(options.get("fornecedores") or []),
            key="exec_supplier",
        )
        selected_category = col_category.selectbox(
            "Categoria",
            options=["Todas"] + list(options.get("categorias") or []),
            key="exec_category",
        )
        selected_service = col_service.selectbox(
            "Serviço",
            options=["Todos"] + list(options.get("servicos") or []),
            key="exec_service",
        )

        filter_group_title("Filtros avançados")
        row_two = st.columns(4, gap="large")
        selected_city = row_two[0].selectbox(
            "Cidade",
            options=["Todas"] + list(options.get("cidades") or []),
            key="exec_city",
        )
        selected_cost_center = row_two[1].selectbox(
            "Centro de custo",
            options=["Todos"] + list(options.get("centros_custo") or []),
            key="exec_cost_center",
        )
        min_amount = row_two[2].number_input(
            "Valor inicial",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="exec_min_amount",
        )
        max_amount = row_two[3].number_input(
            "Valor final",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="exec_max_amount",
        )

        row_three = st.columns(3, gap="large")
        start_date = row_three[0].date_input("Data inicial", value=None, key="exec_start_date")
        end_date = row_three[1].date_input("Data final", value=None, key="exec_end_date")
        presentation_mode = row_three[2].toggle(
            "Modo apresentação",
            key="exec_presentation",
            help="Oculta detalhes secundários e aumenta o foco dos blocos executivos.",
        )
        refresh_clicked, clear_clicked = action_buttons(
            primary_key="exec_refresh_button",
            secondary_key="exec_clear_button",
        )
        if refresh_clicked:
            _load_dashboard.clear()
            st.rerun()
        if clear_clicked:
            for key in (
                "exec_competence",
                "exec_supplier",
                "exec_category",
                "exec_service",
                "exec_city",
                "exec_cost_center",
                "exec_min_amount",
                "exec_max_amount",
                "exec_start_date",
                "exec_end_date",
            ):
                st.session_state.pop(key, None)
            _load_dashboard.clear()
            st.rerun()

    if min_amount and max_amount and min_amount > max_amount:
        warning_box("Valor inicial não pode ser maior que o valor final. O valor final será ignorado.")
        max_amount = 0.0
    if isinstance(start_date, date) and isinstance(end_date, date) and start_date > end_date:
        warning_box("Data inicial não pode ser maior que a data final. A data final será ignorada.")
        end_date = None

    st.session_state["exec_presentation_active"] = presentation_mode
    return {
        "competencia": selected_competence,
        "fornecedor": selected_supplier,
        "categoria": selected_category,
        "servico": selected_service,
        "cidade": selected_city,
        "centro_custo": selected_cost_center,
        "valor_inicial": min_amount if min_amount > 0 else None,
        "valor_final": max_amount if max_amount > 0 else None,
        "data_inicial": _date_to_api(start_date),
        "data_final": _date_to_api(end_date),
    }


def _render_dashboard(dashboard: dict[str, Any]) -> None:
    """Renderiza todos os blocos executivos."""
    metadata = dashboard.get("metadata") or {}
    last_update = metadata.get("ultima_atualizacao")
    if last_update:
        info_box(f"Última atualização da base: {last_update}")

    _render_kpis(dashboard.get("kpis") or [])
    _render_comparison(dashboard.get("charts") or {})
    _render_categories(dashboard)
    _render_suppliers(dashboard)
    _render_services(dashboard)
    _render_last_entries(dashboard)
    _render_insights(dashboard.get("insights") or [])
    _render_exports(dashboard)


def _render_kpis(kpis: list[dict[str, Any]]) -> None:
    """Renderiza cards executivos."""
    section_title("KPIs", "Indicadores principais com tendência contra a competência anterior.")
    cards = []
    for item in kpis:
        variation = item.get("variacao") or {}
        cards.append(
            {
                "label": str(item.get("titulo") or ""),
                "value": _format_kpi_value(str(item.get("key") or ""), item.get("valor")),
                "icon": str(item.get("icone") or ""),
                "description": f"{item.get('descricao') or ''} | {variation.get('texto') or '0,00%'}",
                "status": _status_to_card_status(str(variation.get("status") or "estavel")),
            },
        )
    render_metric_cards(cards, columns=4)


def _render_comparison(charts: dict[str, Any]) -> None:
    """Renderiza evolução e comparação mensal."""
    section_title("Comparativo", "Evolução mensal e comparação contra a competência anterior.")
    col_evolution, col_comparison = st.columns([2, 1], gap="large")
    with col_evolution:
        executive_monthly_line(charts.get("evolucao_mensal") or [])
    with col_comparison:
        executive_comparison_columns(charts.get("comparacao_mensal") or [])


def _render_categories(dashboard: dict[str, Any]) -> None:
    """Renderiza bloco de categorias."""
    section_title("Categorias", "Top categorias e distribuição proporcional.")
    charts = dashboard.get("charts") or {}
    tables = dashboard.get("tables") or {}
    col_rank, col_share = st.columns([3, 2], gap="large")
    with col_rank:
        executive_horizontal_bar(charts.get("top_categorias") or [], "categoria", "Top 10 categorias")
    with col_share:
        executive_donut(charts.get("distribuicao_categorias") or [], "categoria", "Distribuição das categorias")
    if not st.session_state.get("exec_presentation_active"):
        render_table(
            pd.DataFrame(tables.get("categorias") or []),
            title="Resumo por categoria",
            height=360,
            column_order=("categoria", "valor_total", "quantidade", "ticket_medio", "percentual_sobre_total"),
            hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        )


def _render_suppliers(dashboard: dict[str, Any]) -> None:
    """Renderiza bloco de fornecedores."""
    section_title("Fornecedores", "Concentração de pagamentos por fornecedor.")
    charts = dashboard.get("charts") or {}
    tables = dashboard.get("tables") or {}
    col_rank, col_share = st.columns([3, 2], gap="large")
    with col_rank:
        executive_horizontal_bar(charts.get("top_fornecedores") or [], "fornecedor", "Top 10 fornecedores")
    with col_share:
        executive_donut(charts.get("distribuicao_fornecedores") or [], "fornecedor", "Distribuição dos fornecedores")
    if not st.session_state.get("exec_presentation_active"):
        render_table(
            pd.DataFrame(tables.get("fornecedores") or []),
            title="Resumo por fornecedor",
            height=360,
            column_order=("fornecedor", "valor_total", "quantidade", "ticket_medio", "percentual_sobre_total"),
            hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        )


def _render_services(dashboard: dict[str, Any]) -> None:
    """Renderiza bloco de servicos e cidades."""
    section_title("Serviços", "Serviços mais relevantes e distribuição por cidade.")
    charts = dashboard.get("charts") or {}
    tables = dashboard.get("tables") or {}
    col_services, col_city = card_grid(2)
    with col_services:
        executive_horizontal_bar(charts.get("top_servicos") or [], "servico", "Top 10 serviços")
    with col_city:
        executive_city_bar(charts.get("distribuicao_cidades") or [])
    if not st.session_state.get("exec_presentation_active"):
        render_table(
            pd.DataFrame(tables.get("servicos") or []),
            title="Resumo por serviço",
            height=360,
            column_order=("servico", "valor_total", "quantidade", "ticket_medio", "percentual_sobre_total"),
            hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        )


def _render_last_entries(dashboard: dict[str, Any]) -> None:
    """Renderiza ultimos lancamentos."""
    if st.session_state.get("exec_presentation_active"):
        return
    section_title("Últimos lançamentos", "Registros financeiros mais recentes no filtro atual.")
    entries = pd.DataFrame((dashboard.get("tables") or {}).get("ultimos_lancamentos") or [])
    render_table(
        entries,
        height=420,
        column_order=(
            "fornecedor",
            "valor",
            "categoria",
            "servico",
            "cidade",
            "centro_custo",
            "data_lancamento",
            "documento",
            "descricao",
        ),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
    )


def _render_insights(insights: list[dict[str, Any]]) -> None:
    """Renderiza insights automaticos."""
    section_title("Insights automáticos", "Alertas e leituras gerenciais gerados a partir dos dados filtrados.")
    render_metric_cards(
        [
            {
                "label": str(insight.get("titulo") or ""),
                "value": str(insight.get("descricao") or ""),
                "icon": "!",
                "description": "Insight automático",
                "status": _status_to_card_status(str(insight.get("status") or "neutral")),
            }
            for insight in insights
        ],
        columns=3,
    )


def _render_exports(dashboard: dict[str, Any]) -> None:
    """Renderiza acoes extras de exportacao."""
    if st.session_state.get("exec_presentation_active"):
        return
    section_title("Exportação", "Arquivos gerados a partir dos dados exibidos nesta tela.")
    st.download_button(
        "Exportar Excel",
        data=_dashboard_excel(dashboard),
        file_name="dashboard-executivo-cetel.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )


def _dashboard_excel(dashboard: dict[str, Any]) -> bytes:
    """Gera um XLSX com tabelas principais do dashboard."""
    output = BytesIO()
    tables = dashboard.get("tables") or {}
    charts = dashboard.get("charts") or {}
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(dashboard.get("kpis") or []).to_excel(writer, sheet_name="KPIs", index=False)
        pd.DataFrame(charts.get("evolucao_mensal") or []).to_excel(writer, sheet_name="Evolucao", index=False)
        pd.DataFrame(tables.get("categorias") or []).to_excel(writer, sheet_name="Categorias", index=False)
        pd.DataFrame(tables.get("fornecedores") or []).to_excel(writer, sheet_name="Fornecedores", index=False)
        pd.DataFrame(tables.get("servicos") or []).to_excel(writer, sheet_name="Servicos", index=False)
        pd.DataFrame(tables.get("ultimos_lancamentos") or []).to_excel(writer, sheet_name="Lancamentos", index=False)
    return output.getvalue()


def _format_kpi_value(key: str, value: object) -> str:
    if key in {"total_geral", "total_mes", "ticket_medio"}:
        return _format_currency(value)
    return _format_integer(value)


def _format_currency(value: object) -> str:
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return str(value or "")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_integer(value: object) -> str:
    try:
        return str(int(Decimal(str(value or 0))))
    except (InvalidOperation, ValueError):
        return str(value or "")


def _status_to_card_status(status: str) -> str:
    if status == "aumento":
        return "danger"
    if status == "reducao":
        return "success"
    if status == "warning":
        return "warning"
    return "neutral"


def _date_to_api(value: object) -> str | None:
    return value.isoformat() if isinstance(value, date) else None


if __name__ == "__main__":
    main()
