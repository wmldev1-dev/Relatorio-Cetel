"""Pagina de relatorio por servico."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from components.charts import service_share_chart, service_total_ranking_chart
from components.ui import (
    action_buttons,
    card_grid,
    error_box,
    info_box,
    page_footer,
    page_title,
    render_metric_cards,
    render_table,
    section_title,
)
from services.api_client import (
    APIClientError,
    get_relatorio_servicos,
    listar_competencias,
)

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
    """Renderiza a analise de gastos por servico."""
    page_title("Serviços", "Análise de gastos por serviço.")

    try:
        competences = listar_competencias()
        if not competences:
            info_box("Nenhuma competência registrada para análise.")
            page_footer()
            return

        periods = [item["periodo"] for item in competences]
        selected_competence = _render_competence_filter(periods)
        initial_rows = get_relatorio_servicos(selected_competence, limit=500)
        services = ["Todos"] + [str(row["servico"]) for row in initial_rows]
        selected_service = _render_service_filter(services)
        service_filter = (
            selected_service
            if selected_service and selected_service != "Todos"
            else None
        )
        rows = get_relatorio_servicos(
            competencia=selected_competence,
            servico=service_filter,
            limit=50,
        )
        if not rows:
            info_box("Nenhum dado encontrado para os filtros selecionados.")
            page_footer()
            return

        _render_metrics(rows)
        _render_charts(rows)
        _render_table(rows)
        page_footer()
    except APIClientError as error:
        error_box(f"Não foi possível carregar o relatório por serviço: {error}")
        page_footer()


def _render_competence_filter(periods: list[str]) -> str:
    with st.container(border=True):
        section_title("Filtros principais", "Selecione a competência para carregar os serviços disponíveis.")
        selected_competence = st.selectbox(
            "Competência",
            options=periods,
            help="Competência usada para consolidar os serviços.",
            key="service_report_competence",
        )
        refresh_clicked, clear_clicked = action_buttons(
            primary_key="service_competence_refresh_button",
            secondary_key="service_competence_clear_button",
        )
        if refresh_clicked:
            st.rerun()
        if clear_clicked:
            st.session_state.pop("service_report_competence", None)
            st.rerun()
    return str(selected_competence)


def _render_service_filter(services: list[str]) -> str:
    with st.container(border=True):
        section_title("Filtro de serviço", "Refine o relatório por um serviço específico.")
        selected_service = st.selectbox(
            "Serviço",
            options=services,
            help="Filtre por um serviço específico ou mantenha todos.",
            key="service_report_service",
        )
        refresh_clicked, clear_clicked = action_buttons(
            primary_key="service_refresh_button",
            secondary_key="service_clear_button",
        )
        if refresh_clicked:
            st.rerun()
        if clear_clicked:
            st.session_state.pop("service_report_competence", None)
            st.session_state.pop("service_report_service", None)
            st.rerun()
    return str(selected_service)


def _render_metrics(rows: list[dict[str, Any]]) -> None:
    total = sum((_to_decimal(row.get("total")) for row in rows), Decimal("0.00"))
    quantity = len(rows)
    biggest = max(rows, key=lambda row: _to_decimal(row.get("total")))
    total_entries = sum(int(row.get("quantidade_lancamentos") or 0) for row in rows)
    average = total / total_entries if total_entries else Decimal("0.00")

    render_metric_cards(
        [
            {"label": "Total gasto", "value": _format_currency(total), "icon": "R$", "description": "Soma dos serviços"},
            {"label": "Quantidade de serviços", "value": quantity, "icon": "S", "description": "Serviços no filtro"},
            {
                "label": "Maior serviço",
                "value": str(biggest.get("servico") or ""),
                "icon": "↑",
                "description": _format_currency(biggest.get("total")),
            },
            {"label": "Ticket médio", "value": _format_currency(average), "icon": "M", "description": "Média por lançamento"},
        ],
        columns=4,
    )


def _render_charts(rows: list[dict[str, Any]]) -> None:
    section_title("Visão rápida", "Ranking e participação dos serviços no filtro atual.")
    col_ranking, col_share = card_grid(2)
    with col_ranking:
        service_total_ranking_chart(rows)
    with col_share:
        service_share_chart(rows)


def _render_table(rows: list[dict[str, Any]]) -> None:
    section_title("Tabela detalhada", "Colunas priorizadas para análise gerencial.")
    frame = pd.DataFrame(rows)
    render_table(
        frame,
        height=500,
        column_order=(
            "servico",
            "total",
            "quantidade_lancamentos",
            "ticket_medio",
            "percentual_sobre_total",
        ),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        caption="Ranking consolidado por serviço dentro da competência selecionada.",
    )


def _to_decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _format_currency(value: object) -> str:
    amount = _to_decimal(value)
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    main()
