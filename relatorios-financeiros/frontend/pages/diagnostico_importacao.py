"""Pagina de diagnostico das importacoes SQL."""

from __future__ import annotations

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
    success_box,
    warning_box,
)
from services.api_client import (
    APIClientError,
    listar_importacoes,
    obter_diagnostico_importacao,
)


def main() -> None:
    """Renderiza a tela de diagnostico de importacao."""
    page_title(
        "Diagnóstico de Importação",
        "Acompanhe parsing, gravação e qualidade do mapeamento dos lotes.",
    )

    try:
        imports = listar_importacoes()
        if not imports:
            info_box("Nenhuma importação registrada.")
            page_footer()
            return

        options = {
            (
                f"{item['id_importacao']} - {item['competencia']} - "
                f"{item['arquivo_original']} - {item['status']}"
            ): int(item["id_importacao"])
            for item in imports
        }
        with st.container(border=True):
            section_title(
                "Filtro do diagnóstico",
                "Selecione o lote que será analisado.",
            )
            selected_label = st.selectbox(
                "Importação",
                options=list(options.keys()),
                help="Lote de importação usado para montar o diagnóstico.",
                key="diagnostic_import",
            )
            refresh_clicked, clear_clicked = action_buttons(
                primary_key="diagnostic_import_refresh_button",
                secondary_key="diagnostic_import_clear_button",
            )
            if refresh_clicked:
                st.rerun()
            if clear_clicked:
                st.session_state.pop("diagnostic_import", None)
                st.rerun()
        diagnostics = obter_diagnostico_importacao(options[selected_label])

        _render_metadata(diagnostics)
        _render_counts(diagnostics)
        _render_parse_details(diagnostics)
        _render_previews(diagnostics)
        _render_quality_checks(diagnostics)
        page_footer()
    except (APIClientError, ValueError) as error:
        error_box(f"Não foi possível gerar o diagnóstico: {error}")
        page_footer()


def _render_metadata(diagnostics: dict[str, object]) -> None:
    """Exibe metadados do lote importado."""
    section_title("Lote", "Dados gerais da importação selecionada.")
    render_metric_cards(
        [
            {"label": "Status", "value": str(diagnostics["status"]), "icon": "S", "description": "Situação do lote"},
            {"label": "Arquivo", "value": str(diagnostics["source_file"]), "icon": "A", "description": "Origem do processamento"},
            {"label": "Competência", "value": str(diagnostics["competence"]), "icon": "C", "description": "Período associado"},
        ],
        columns=3,
    )

    if diagnostics.get("error_message"):
        error_box(str(diagnostics["error_message"]))

    if not diagnostics.get("file_exists"):
        warning_box("O arquivo físico da importação não foi encontrado.")


def _render_counts(diagnostics: dict[str, object]) -> None:
    """Exibe contadores principais do diagnostico."""
    section_title("Contadores", "Volume identificado no SQL e gravado na base.")
    render_metric_cards(
        [
            {"label": "INSERTs encontrados", "value": diagnostics["insert_count"], "icon": "I", "description": "Comandos SQL identificados"},
            {"label": "Registros extraídos", "value": diagnostics["extracted_count"], "icon": "E", "description": "Linhas lidas do arquivo"},
            {"label": "Registros gravados", "value": diagnostics["saved_count"], "icon": "G", "description": "Linhas persistidas"},
        ],
        columns=3,
    )


def _render_parse_details(diagnostics: dict[str, object]) -> None:
    """Exibe detalhes tecnicos do parser."""
    section_title("Estrutura extraída")
    tables = diagnostics.get("tables") or []
    columns = diagnostics.get("columns") or []

    section_title("Tabelas encontradas")
    if tables:
        table_frame = pd.DataFrame({"tabela": tables})
        render_table(table_frame, height=240)
    else:
        info_box("Nenhuma tabela identificada em comandos INSERT.")

    section_title("Colunas encontradas")
    if columns:
        column_frame = pd.DataFrame({"coluna": columns})
        render_table(column_frame, height=300)
    else:
        info_box("Nenhuma coluna identificada.")


def _render_previews(diagnostics: dict[str, object]) -> None:
    """Exibe amostras dos dados extraidos e gravados."""
    section_title("Prévia dos dados")
    extracted_preview = diagnostics.get("extracted_preview") or []
    saved_preview = diagnostics.get("saved_preview") or []

    section_title("Primeiras 20 linhas extraídas do SQL")
    if extracted_preview:
        extracted_frame = pd.DataFrame(extracted_preview)
        render_table(
            extracted_frame,
            height=360,
        )
    else:
        info_box("Nenhum registro extraído para prévia.")

    section_title("Primeiras 20 linhas gravadas em financial_entries")
    if saved_preview:
        saved_frame = pd.DataFrame(saved_preview)
        render_table(
            saved_frame,
            height=360,
        )
    else:
        info_box("Nenhum lançamento gravado para prévia.")


def _render_quality_checks(diagnostics: dict[str, object]) -> None:
    """Exibe campos nao mapeados e vazios importantes."""
    section_title("Qualidade do mapeamento")
    unmapped_fields = diagnostics.get("unmapped_fields") or []
    empty_important_fields = diagnostics.get("empty_important_fields") or []

    section_title("Campos não mapeados")
    if unmapped_fields:
        unmapped_frame = pd.DataFrame({"campo_nao_mapeado": unmapped_fields})
        render_table(
            unmapped_frame,
            height=260,
        )
    else:
        success_box("Nenhum campo não mapeado encontrado.")

    section_title("Possíveis campos vazios importantes")
    if empty_important_fields:
        empty_fields_frame = pd.DataFrame(empty_important_fields)
        render_table(
            empty_fields_frame,
            height=300,
        )
    else:
        info_box("Nenhum campo importante avaliado.")


if __name__ == "__main__":
    main()
