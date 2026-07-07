"""Pagina de diagnostico de campos financeiros."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from components.ui import (
    action_buttons,
    card_grid,
    error_box,
    info_box,
    page_footer,
    page_title,
    primary_button,
    render_metric_cards,
    render_table,
    section_title,
    warning_box,
)
from services.api_client import (
    APIClientError,
    listar_competencias,
    listar_importacoes,
    obter_diagnostico_campos,
    reprocessar_importacao,
)


def main() -> None:
    """Renderiza diagnostico de preenchimento dos campos financeiros."""
    page_title(
        "Diagnóstico de Campos",
        "Identifique campos financeiros vazios e candidatos de mapeamento.",
    )

    try:
        competences = listar_competencias()
        if not competences:
            info_box("Nenhuma competência registrada para diagnóstico.")
            page_footer()
            return

        periods = [item["periodo"] for item in competences]
        with st.container(border=True):
            section_title("Filtro", "Selecione a competência que será analisada.")
            selected_competence = st.selectbox(
                "Competência",
                options=periods,
                help="Competência usada para calcular preenchimento e ler o SQL de origem.",
                key="field_diagnostic_competence",
            )
            refresh_clicked, clear_clicked = action_buttons(
                primary_key="field_diagnostic_refresh_button",
                secondary_key="field_diagnostic_clear_button",
            )
            if refresh_clicked:
                st.rerun()
            if clear_clicked:
                st.session_state.pop("field_diagnostic_competence", None)
                st.rerun()

        diagnostics = obter_diagnostico_campos(selected_competence)
        _render_reprocess_action(selected_competence)
        _render_quality_cards(diagnostics)
        _render_field_fill_table(diagnostics)
        _render_service_alert(diagnostics)
        _render_samples(diagnostics)
        _render_mapping_details(diagnostics)
        page_footer()
    except APIClientError as error:
        error_box(f"Não foi possível carregar o diagnóstico de campos: {error}")
        page_footer()


def _render_reprocess_action(selected_competence: str) -> None:
    warning_box(
        "Para aplicar novo mapeamento, reprocese o lote da competência. "
        "O reprocessamento apaga e recria apenas os lançamentos do lote selecionado.",
    )

    imports = listar_importacoes()
    import_batch = _find_import_batch(imports, selected_competence)
    if import_batch is None:
        info_box("Nenhum lote de importação encontrado para esta competência.")
        return

    batch_id = int(import_batch["id_importacao"])
    with st.container(border=True):
        section_title(
            "Reprocessamento",
            (
                f"Lote #{batch_id} - {import_batch.get('arquivo_original', '')} "
                f"({import_batch.get('status', '')})"
            ),
        )
        if primary_button("Reprocessar lote", key="field_reprocess_button", icon="↻"):
            try:
                result = reprocessar_importacao(batch_id)
                st.success(result.get("message", "Lote reprocessado com sucesso."))
                st.rerun()
            except APIClientError as error:
                error_box(f"Não foi possível reprocessar o lote: {error}")


def _render_quality_cards(diagnostics: dict[str, Any]) -> None:
    fill_by_field = _fill_by_field(diagnostics)
    service_fill = _percent(fill_by_field.get("service", {}))
    supplier_fill = _percent(fill_by_field.get("supplier", {}))
    category_fill = _percent(fill_by_field.get("category", {}))

    render_metric_cards(
        [
            {
                "label": "Total de lançamentos",
                "value": diagnostics.get("total_lancamentos", 0),
                "icon": "T",
                "description": "Registros gravados na competência",
            },
            {"label": "Serviço preenchido", "value": f"{service_fill:.2f}%", "icon": "S", "description": "Campo service"},
            {"label": "Fornecedor preenchido", "value": f"{supplier_fill:.2f}%", "icon": "F", "description": "Campo supplier"},
            {"label": "Categoria preenchida", "value": f"{category_fill:.2f}%", "icon": "C", "description": "Campo category"},
        ],
        columns=4,
    )


def _render_field_fill_table(diagnostics: dict[str, Any]) -> None:
    section_title("Preenchimento por campo")
    frame = pd.DataFrame(diagnostics.get("preenchimento") or [])
    render_table(
        frame,
        height=320,
        column_order=(
            "campo",
            "percentual_preenchido",
            "quantidade_preenchida",
            "quantidade_vazia",
        ),
    )


def _render_service_alert(diagnostics: dict[str, Any]) -> None:
    service_info = _fill_by_field(diagnostics).get("service", {})
    if _percent(service_info) == 0 and diagnostics.get("total_lancamentos", 0):
        warning_box(
            "O campo service está 0% preenchido nesta competência. "
            "Revise as colunas candidatas abaixo antes de alterar o mapeamento.",
        )


def _render_samples(diagnostics: dict[str, Any]) -> None:
    section_title("Amostras")
    original_samples = diagnostics.get("amostra_registros_originais") or []
    saved_samples = diagnostics.get("amostra_lancamentos_gravados") or []

    col_original, col_saved = card_grid(2)
    with col_original:
        section_title("Registros originais relevantes")
        if original_samples:
            frame = pd.DataFrame(original_samples)
            render_table(frame, height=420)
        else:
            info_box("Nenhum registro original disponível para amostra.")

    with col_saved:
        section_title("Lançamentos gravados")
        if saved_samples:
            frame = pd.DataFrame(saved_samples)
            render_table(
                frame,
                height=420,
                column_order=(
                    "fornecedor",
                    "valor",
                    "categoria",
                    "servico",
                    "data_lancamento",
                    "documento",
                    "usuario",
                    "descricao",
                ),
            )
        else:
            info_box("Nenhum lançamento gravado encontrado.")


def _render_mapping_details(diagnostics: dict[str, Any]) -> None:
    section_title("Mapeamento do SQL")
    col_columns, col_unmapped, col_candidates = card_grid(3)
    with col_columns:
        _render_list_table(
            "Colunas de origem detectadas",
            "coluna",
            diagnostics.get("colunas_origem_detectadas") or [],
        )
    with col_unmapped:
        _render_list_table(
            "Campos não mapeados",
            "campo_nao_mapeado",
            diagnostics.get("campos_nao_mapeados") or [],
        )
    with col_candidates:
        _render_list_table(
            "Candidatos para serviço",
            "campo_candidato",
            diagnostics.get("sugestoes_campos_servico") or [],
        )


def _render_list_table(title: str, column: str, values: list[str]) -> None:
    section_title(title)
    if not values:
        info_box("Nenhum item encontrado.")
        return
    frame = pd.DataFrame({column: values})
    render_table(frame, height=320)


def _fill_by_field(diagnostics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("campo")): item
        for item in diagnostics.get("preenchimento", [])
    }


def _percent(item: dict[str, Any]) -> Decimal:
    return Decimal(str(item.get("percentual_preenchido") or 0))


def _find_import_batch(
    imports: list[dict[str, Any]],
    selected_competence: str,
) -> dict[str, Any] | None:
    for item in imports:
        if item.get("competencia") == selected_competence:
            return item
    return None


if __name__ == "__main__":
    main()
