"""Pagina de comparativo mensal de gastos."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from components.charts import comparison_bar_chart, ranking_horizontal_bar_chart
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
    get_comparativo_mensal,
    listar_competencias,
)

MANAGEMENT_HIDDEN_COLUMNS = (
    "id",
    "competence_id",
    "import_batch_id",
    "id_importacao",
    "created_at",
    "updated_at",
)


def main() -> None:
    """Renderiza a tela de comparativo mensal."""
    page_title(
        "Comparativo Mensal",
        "Compare gastos entre duas competências.",
    )

    try:
        competences = listar_competencias()
        if not competences:
            info_box("Nenhuma competência registrada para comparação.")
            page_footer()
            return

        periods = [item["periodo"] for item in competences]
        base_default = 1 if len(periods) > 1 else 0
        comparison_default = 0

        with st.container(border=True):
            section_title(
                "Filtros",
                "Selecione as competências que serão comparadas.",
            )
            col_base, col_comparison = st.columns(2, gap="large")
            competencia_base = col_base.selectbox(
                "Competência base",
                options=periods,
                index=base_default,
                help="Mês usado como referência inicial.",
                key="comparison_base",
            )
            competencia_comparacao = col_comparison.selectbox(
                "Competência comparação",
                options=periods,
                index=comparison_default,
                help="Mês comparado contra a competência base.",
                key="comparison_target",
            )
            refresh_clicked, clear_clicked = action_buttons(
                primary_key="comparison_refresh_button",
                secondary_key="comparison_clear_button",
            )
            if refresh_clicked:
                st.rerun()
            if clear_clicked:
                st.session_state.pop("comparison_base", None)
                st.session_state.pop("comparison_target", None)
                st.rerun()

        if not competencia_base or not competencia_comparacao:
            info_box("Selecione as duas competências para gerar o comparativo.")
            page_footer()
            return

        comparison = get_comparativo_mensal(
            competencia_base,
            competencia_comparacao,
        )
        _render_summary(comparison)
        _render_rankings(comparison)
        page_footer()
    except APIClientError as error:
        error_box(f"Não foi possível carregar o comparativo mensal: {error}")
        page_footer()


def _render_summary(comparison: dict[str, Any]) -> None:
    """Renderiza cards principais do comparativo."""
    status = str(comparison.get("status") or "estavel")
    status_label = {
        "aumento": "Aumento",
        "reducao": "Redução",
        "estavel": "Estável",
    }.get(status, "Estável")

    section_title(
        "Resumo da comparação",
        f"{comparison['competencia_base']} x {comparison['competencia_comparacao']}",
    )
    render_metric_cards(
        [
            {
                "label": "Total competência base",
                "value": _format_currency(comparison.get("total_base")),
                "icon": "B",
                "description": f"{comparison.get('total_lancamentos_base', 0)} lançamentos",
            },
            {
                "label": "Total competência comparação",
                "value": _format_currency(comparison.get("total_comparacao")),
                "icon": "C",
                "description": f"{comparison.get('total_lancamentos_comparacao', 0)} lançamentos",
            },
            {
                "label": "Diferença em R$",
                "value": _format_currency(comparison.get("diferenca_valor")),
                "icon": _status_icon(status),
                "description": status_label,
                "status": _metric_status(status),
            },
            {
                "label": "Diferença em %",
                "value": _format_percent(comparison.get("diferenca_percentual")),
                "icon": "%",
                "description": "Variação sobre a base",
                "status": _metric_status(status),
            },
        ],
        columns=4,
    )
    comparison_bar_chart(
        str(comparison["competencia_base"]),
        comparison.get("total_base"),
        str(comparison["competencia_comparacao"]),
        comparison.get("total_comparacao"),
    )


def _render_rankings(comparison: dict[str, Any]) -> None:
    """Renderiza rankings de maiores aumentos e reducoes."""
    groups = [
        (
            "Fornecedores",
            "fornecedores_maior_aumento",
            "fornecedores_maior_reducao",
        ),
        ("Serviços", "servicos_maior_aumento", "servicos_maior_reducao"),
        ("Categorias", "categorias_maior_aumento", "categorias_maior_reducao"),
    ]

    for title, increase_key, reduction_key in groups:
        section_title(title)
        if title == "Fornecedores":
            _render_ranking_block(
                "Maior aumento",
                comparison.get(increase_key) or [],
                show_chart=True,
            )
            _render_ranking_block(
                "Maior redução",
                comparison.get(reduction_key) or [],
                show_chart=True,
            )
            continue

        col_increase, col_reduction = card_grid(2)
        with col_increase:
            _render_ranking_block(
                "Maior aumento",
                comparison.get(increase_key) or [],
                show_chart=title in {"Serviços"},
            )
        with col_reduction:
            _render_ranking_block(
                "Maior redução",
                comparison.get(reduction_key) or [],
                show_chart=title in {"Serviços"},
            )


def _render_ranking_block(
    title: str,
    rows: list[dict[str, Any]],
    show_chart: bool,
) -> None:
    section_title(title)
    if not rows:
        info_box("Nenhum dado encontrado para este ranking.")
        return

    if show_chart:
        ranking_horizontal_bar_chart(rows, title)
    frame = pd.DataFrame(rows)
    render_table(
        frame,
        height=320,
        column_order=(
            "nome",
            "valor_base",
            "valor_comparacao",
            "diferenca_valor",
            "diferenca_percentual",
            "quantidade_lancamentos",
        ),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
        caption="A variação positiva indica aumento; variação negativa indica redução.",
    )


def _format_currency(value: object) -> str:
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_percent(value: object) -> str:
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    return f"{amount:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def _status_icon(status: str) -> str:
    if status == "aumento":
        return "↑"
    if status == "reducao":
        return "↓"
    return "="


def _metric_status(status: str) -> str:
    if status == "aumento":
        return "danger"
    if status == "reducao":
        return "success"
    return "neutral"


if __name__ == "__main__":
    main()
