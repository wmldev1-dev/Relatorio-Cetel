"""Pagina de importacao mensal de arquivos SQL."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import (
    action_buttons,
    danger_button,
    error_box,
    info_box,
    page_footer,
    page_title,
    primary_button,
    render_table,
    section_title,
    success_box,
    warning_box,
)
from services.api_client import (
    APIClientError,
    criar_importacao,
    listar_importacoes,
    processar_importacao,
    remover_importacao,
)

STATUS_PENDING = "pending"


def main() -> None:
    """Renderiza a tela de importacao mensal."""
    page_title(
        "Importação Mensal",
        "Registre e acompanhe os lotes mensais de importação SQL.",
    )

    with st.container(border=True):
        section_title("1. Novo lote", "Informe a competência e envie o arquivo da importação mensal.")
        with st.form("monthly_import_form", clear_on_submit=False):
            competence = st.text_input(
                "Competência",
                placeholder="YYYY-MM",
                help="Informe a competência mensal no formato YYYY-MM.",
            )
            uploaded_file = st.file_uploader(
                "Arquivo SQL ou bruto",
                type=None,
                accept_multiple_files=False,
                help="Envie um arquivo .sql ou texto bruto tabulado da competência informada.",
            )
            submitted = st.form_submit_button("REGISTRAR IMPORTAÇÃO", type="primary")

    if submitted:
        try:
            result = criar_importacao(competence, uploaded_file)
            st.session_state["last_import_batch_id"] = result["import_batch_id"]
            success_box(result["message"])
        except APIClientError as error:
            error_box(str(error))

    last_import_batch_id = st.session_state.get("last_import_batch_id")
    if last_import_batch_id:
        info_box(
            f"Importação {last_import_batch_id} registrada "
            "e pronta para processamento.",
        )
        if primary_button("Processar SQL", key="process_last_import_button", icon="▶"):
            try:
                result = processar_importacao(int(last_import_batch_id))
                success_box(result["message"])
                st.session_state.pop("last_import_batch_id", None)
            except APIClientError as error:
                error_box(str(error))

    section_title("Importações registradas", "Histórico dos lotes enviados.")

    try:
        imports = listar_importacoes()
        if imports:
            pending_imports = [
                item for item in imports
                if item["status"] == STATUS_PENDING
            ]
            if pending_imports:
                options = {
                    (
                        f"{item['id_importacao']} - {item['competencia']} - "
                        f"{item['arquivo_original']}"
                    ): int(item["id_importacao"])
                    for item in pending_imports
                }
                with st.container(border=True):
                    section_title(
                        "2. Processamento pendente",
                        "Selecione um lote registrado para processar.",
                    )
                    selected_import = st.selectbox(
                        "Importação pendente",
                        options=list(options.keys()),
                        help="Selecione um lote pendente para processar.",
                        key="pending_import",
                    )
                    process_clicked, refresh_clicked = action_buttons(
                        primary_label="PROCESSAR SQL",
                        secondary_label="ATUALIZAR",
                        primary_key="pending_process_button",
                        secondary_key="pending_refresh_button",
                    )
                    if process_clicked:
                        try:
                            result = processar_importacao(options[selected_import])
                            success_box(result["message"])
                        except APIClientError as error:
                            error_box(str(error))
                    if refresh_clicked:
                        st.rerun()

            _render_remove_import(imports)
            imports_frame = pd.DataFrame(imports)
            render_table(
                imports_frame,
                height=420,
                column_order=(
                    "id_importacao",
                    "competencia",
                    "status",
                    "arquivo_original",
                    "records_count",
                    "created_at",
                    "mensagem_erro",
                ),
                caption="Histórico dos lotes registrados para auditoria e acompanhamento.",
            )
        else:
            info_box("Nenhuma importação registrada.")
        page_footer()
    except APIClientError as error:
        error_box(f"Não foi possível carregar as importações: {error}")
        page_footer()


def _render_remove_import(imports: list[dict[str, object]]) -> None:
    with st.container(border=True):
        section_title(
            "3. Remover importação",
            "Apague do banco o lote selecionado e todos os lançamentos vinculados.",
        )
        warning_box(
            "Esta ação remove os registros da importação e os lançamentos financeiros "
            "associados. O arquivo SQL original não é alterado.",
        )

        options = {
            (
                f"{item['id_importacao']} - {item['competencia']} - "
                f"{item['arquivo_original']} ({item['status']})"
            ): int(item["id_importacao"])
            for item in imports
        }
        selected_import = st.selectbox(
            "Importação para remover",
            options=list(options.keys()),
            help="Selecione o lote que será removido do banco de dados.",
            key="remove_import_batch",
        )
        confirm = st.checkbox(
            "Confirmo que desejo remover esta importação e seus lançamentos.",
            key="confirm_remove_import_batch",
        )
        if danger_button(
            "Remover importação",
            key="remove_import_button",
            disabled=not confirm,
        ):
            try:
                result = remover_importacao(options[selected_import])
                success_box(result["message"])
                st.rerun()
            except APIClientError as error:
                error_box(str(error))


if __name__ == "__main__":
    main()
