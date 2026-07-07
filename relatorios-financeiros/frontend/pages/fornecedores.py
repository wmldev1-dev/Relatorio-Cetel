"""Pagina de relatorio por fornecedor."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from components.charts import supplier_share_chart, supplier_total_ranking_chart
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
    get_relatorio_fornecedores,
    listar_competencias,
    listar_fornecedores,
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
    """Renderiza a analise de gastos por fornecedor."""
    page_title("Fornecedores", "Análise de gastos por fornecedor.")

    try:
        competences = listar_competencias()
        if not competences:
            info_box("Nenhuma competência registrada para análise.")
            page_footer()
            return

        periods = [item["periodo"] for item in competences]
        suppliers = ["Todos"] + listar_fornecedores()
        with st.container(border=True):
            section_title("Filtros", "Selecione primeiro a competência e depois refine por fornecedor.")
            col_competence, col_supplier = st.columns(2, gap="large")
            selected_competence = col_competence.selectbox(
                "Competência",
                options=periods,
                help="Competência usada para consolidar os fornecedores.",
                key="supplier_report_competence",
            )
            selected_supplier = col_supplier.selectbox(
                "Fornecedor",
                options=suppliers,
                help="Filtre por um fornecedor específico ou mantenha todos.",
                key="supplier_report_supplier",
            )
            refresh_clicked, clear_clicked = action_buttons(
                primary_key="supplier_refresh_button",
                secondary_key="supplier_clear_button",
            )
            if refresh_clicked:
                st.rerun()
            if clear_clicked:
                st.session_state.pop("supplier_report_competence", None)
                st.session_state.pop("supplier_report_supplier", None)
                st.rerun()

        supplier_filter = (
            selected_supplier
            if selected_supplier and selected_supplier != "Todos"
            else None
        )
        rows = get_relatorio_fornecedores(
            competencia=selected_competence,
            fornecedor=supplier_filter,
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
        error_box(f"Não foi possível carregar o relatório por fornecedor: {error}")
        page_footer()


def _render_metrics(rows: list[dict[str, Any]]) -> None:
    total = sum((_to_decimal(row.get("total")) for row in rows), Decimal("0.00"))
    quantity = len(rows)
    biggest = max(rows, key=lambda row: _to_decimal(row.get("total")))
    total_entries = sum(int(row.get("quantidade_lancamentos") or 0) for row in rows)
    average = total / total_entries if total_entries else Decimal("0.00")

    render_metric_cards(
        [
            {"label": "Total gasto", "value": _format_currency(total), "icon": "R$", "description": "Soma dos fornecedores"},
            {"label": "Quantidade de fornecedores", "value": quantity, "icon": "F", "description": "Fornecedores no filtro"},
            {
                "label": "Maior fornecedor",
                "value": str(biggest.get("fornecedor") or ""),
                "icon": "↑",
                "description": _format_currency(biggest.get("total")),
            },
            {"label": "Ticket médio geral", "value": _format_currency(average), "icon": "M", "description": "Média por lançamento"},
        ],
        columns=4,
    )


def _render_charts(rows: list[dict[str, Any]]) -> None:
    section_title("Visão rápida", "Ranking e participação dos fornecedores no filtro atual.")
    col_ranking, col_share = card_grid(2)
    with col_ranking:
        supplier_total_ranking_chart(rows)
    with col_share:
        supplier_share_chart(rows)


def _render_table(rows: list[dict[str, Any]]) -> None:
    section_title("Tabela detalhada", "Colunas priorizadas para análise gerencial.")
    frame = pd.DataFrame(rows)
    render_table(
        frame,
        height=500,
        column_order=(
            "fornecedor",
            "total",
            "quantidade_lancamentos",
            "ticket_medio",
            "percentual_sobre_total",
        ),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        caption="Ranking consolidado por fornecedor dentro da competência selecionada.",
    )


def _to_decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _format_currency(value: object) -> str:
    amount = _to_decimal(value)
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    main()
