"""Pagina de consulta dos lancamentos financeiros consolidados."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import streamlit as st

from components.ui import (
    action_buttons,
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
    listar_categorias,
    listar_competencias,
    listar_fornecedores,
    listar_usuarios,
    obter_competencia,
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
    """Renderiza a tela de dados financeiros por competencia."""
    page_title(
        "Dados Financeiros",
        "Consulta consolidada dos lançamentos por competência.",
    )

    try:
        options = listar_competencias()
        if not options:
            info_box("Nenhuma competência registrada.")
            page_footer()
            return

        option_labels = {item["periodo"]: item["id"] for item in options}
        with st.container(border=True):
            section_title(
                "Filtros da consulta",
                "Escolha a competência e refine os lançamentos exibidos.",
            )
            selected_period = st.selectbox(
                "Competência",
                options=list(option_labels.keys()),
                help="Competência financeira usada para carregar o resumo.",
                key="financial_competence",
            )
            refresh_clicked, clear_clicked = action_buttons(
                primary_key="financial_refresh_button",
                secondary_key="financial_clear_button",
            )
            if refresh_clicked:
                st.rerun()
            if clear_clicked:
                for key in (
                    "financial_competence",
                    "financial_supplier",
                    "financial_category",
                    "financial_user",
                ):
                    st.session_state.pop(key, None)
                st.rerun()
        competence_id = option_labels[selected_period]
        overview = obter_competencia(competence_id)

        render_metric_cards(
            [
                {
                    "label": "Quantidade de lançamentos",
                    "value": overview["count"],
                    "icon": "Q",
                    "description": "Registros da competência",
                },
                {
                    "label": "Valor total",
                    "value": _format_currency(overview["total"]),
                    "icon": "R$",
                    "description": "Total consolidado",
                },
            ],
            columns=2,
        )

        section_title(
            "Lançamentos da competência",
            "Use os filtros para refinar a lista exibida.",
        )
        entries = overview["entries"]
        if entries:
            entries_frame = pd.DataFrame(entries)
            suppliers = ["Todos"] + listar_fornecedores()
            categories = ["Todas"] + listar_categorias()
            users = ["Todos"] + listar_usuarios()

            with st.container(border=True):
                section_title("Filtros avançados", "Refine a competência por fornecedor, categoria e usuário.")
                filter_supplier, filter_category, filter_user = st.columns(3, gap="large")
                selected_supplier = filter_supplier.selectbox(
                    "Fornecedor",
                    options=suppliers,
                    help="Mostra somente lançamentos do fornecedor selecionado.",
                    key="financial_supplier",
                )
                selected_category = filter_category.selectbox(
                    "Categoria",
                    options=categories,
                    help="Mostra somente lançamentos da categoria selecionada.",
                    key="financial_category",
                )
                selected_user = filter_user.selectbox(
                    "Usuário",
                    options=users,
                    help="Mostra somente lançamentos do usuário selecionado.",
                    key="financial_user",
                )
                refresh_clicked, clear_clicked = action_buttons(
                    primary_key="financial_advanced_refresh_button",
                    secondary_key="financial_advanced_clear_button",
                )
                if refresh_clicked:
                    st.rerun()
                if clear_clicked:
                    for key in (
                        "financial_supplier",
                        "financial_category",
                        "financial_user",
                    ):
                        st.session_state.pop(key, None)
                    st.rerun()

            if selected_supplier != "Todos":
                entries_frame = entries_frame[
                    entries_frame["fornecedor"] == selected_supplier
                ]
            if selected_category != "Todas":
                entries_frame = entries_frame[
                    entries_frame["categoria"] == selected_category
                ]
            if selected_user != "Todos":
                entries_frame = entries_frame[
                    entries_frame["usuario"] == selected_user
                ]

            render_table(
                entries_frame,
                height=560,
                column_order=(
                    "fornecedor",
                    "valor",
                    "categoria",
                    "servico",
                    "data_lancamento",
                    "data_pagamento",
                    "documento",
                    "usuario",
                    "descricao",
                ),
                hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
                caption="Use a rolagem horizontal para conferir campos longos quando necessário.",
            )
        else:
            info_box("Nenhum lançamento encontrado para esta competência.")
        page_footer()
    except APIClientError as error:
        error_box(f"Não foi possível carregar os dados financeiros: {error}")
        page_footer()
    except ValueError as error:
        error_box(str(error))
        page_footer()


def _format_currency(value: object) -> str:
    """Formata valores monetarios para exibicao."""
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    main()
