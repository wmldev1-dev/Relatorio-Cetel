"""Dashboard financeiro principal do Streamlit."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.ui import (
    apply_global_styles,
    card_grid,
    error_box,
    filter_group_title,
    filter_header,
    info_box,
    page_footer,
    page_title,
    primary_button,
    render_metric_cards,
    render_table,
    section_title,
    secondary_button,
    success_box,
    warning_box,
)
from pages import (
    comparativo_mensal,
    dashboard,
    dados_financeiros,
    diagnostico_campos,
    diagnostico_importacao,
    fornecedores,
    importacao,
    servicos,
)
from services.api_client import (
    APIClientError,
    listar_dashboard_financeiro,
    listar_importacoes,
    obter_diagnostico_importacao,
    testar_conexao,
)
CHART_COLORS = ["#3B82F6", "#06B6D4", "#8B5CF6", "#F59E0B", "#22C55E", "#EF4444"]
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


def dashboard_page() -> None:
    """Renderiza o dashboard financeiro."""
    page_header = page_title
    page_header(
        "Dashboard Financeiro",
        "Visão executiva dos lançamentos, rankings e diagnósticos financeiros.",
        badge="LIGHT BI",
    )
    try:
        with st.spinner("Carregando indicadores..."):
            initial_dashboard = listar_dashboard_financeiro()
            filters = _render_filters(initial_dashboard["filters"])
            dashboard = listar_dashboard_financeiro(filters)
        _render_dashboard(dashboard)
    except APIClientError as error:
        error_box(f"Não foi possível carregar o dashboard: {error}")
        page_footer()


def main() -> None:
    """Frame principal com navegacao nativa do Streamlit."""
    st.set_page_config(
        page_title="Relatorios Financeiros CETEL",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_global_styles()

    pages = {
        "ANÁLISES": [
            st.Page(
                dashboard.main,
                title="Dashboard Executivo",
                icon="📊",
                url_path="dashboard-executivo",
                default=True,
            ),
            st.Page(
                dashboard_page,
                title="Dashboard Financeiro",
                icon="📊",
                url_path="dashboard-financeiro",
            ),
            st.Page(
                comparativo_mensal.main,
                title="Comparativo Mensal",
                icon="📈",
                url_path="comparativo-mensal",
            ),
            st.Page(
                fornecedores.main,
                title="Fornecedores",
                icon="🏢",
                url_path="fornecedores",
            ),
            st.Page(
                servicos.main,
                title="Serviços",
                icon="🧾",
                url_path="servicos",
            ),
            st.Page(
                dados_financeiros.main,
                title="Dados Financeiros",
                icon="📋",
                url_path="dados-financeiros",
            ),
        ],
        "IMPORTAÇÃO": [
            st.Page(
                importacao.main,
                title="Importação Mensal",
                icon="📥",
                url_path="importacao",
            ),
            st.Page(
                diagnostico_importacao.main,
                title="Diagnóstico de Importação",
                icon="🔎",
                url_path="diagnostico-importacao",
            ),
            st.Page(
                diagnostico_campos.main,
                title="Diagnóstico de Campos",
                icon="🧭",
                url_path="diagnostico-campos",
            ),
        ],
    }
    pg = st.navigation(pages)
    pg.run()


def _render_filters(options: dict[str, list[Any]]) -> dict[str, Any]:
    """Renderiza filtros globais do dashboard."""
    with st.sidebar:
        filter_header("Filtros do dashboard", "Refine a visão executiva sem sair da página.")

        filter_group_title("1. Período")
        competences = options.get("competencias") or []
        competence_options = {"Todas": None}
        competence_options.update(
            {item["periodo"]: item["id"] for item in competences},
        )
        selected_competence = st.selectbox(
            "Competência",
            options=list(competence_options.keys()),
            help="Selecione uma competência ou mantenha todas.",
            key="dashboard_competence",
        )

        start_date = st.date_input("Data inicial", value=None, key="dashboard_start")
        end_date = st.date_input("Data final", value=None, key="dashboard_end")

        filter_group_title("2. Classificação")
        selected_supplier = st.selectbox(
            "Fornecedor",
            options=["Todos"] + list(options.get("fornecedores") or []),
            help="Filtre por fornecedor quando necessário.",
            key="dashboard_supplier",
        )
        selected_category = st.selectbox(
            "Categoria",
            options=["Todas"] + list(options.get("categorias") or []),
            help="Filtre os lançamentos por categoria.",
            key="dashboard_category",
        )
        selected_user = st.selectbox(
            "Usuário",
            options=["Todos"] + list(options.get("usuarios") or []),
            help="Filtre por usuário responsável.",
            key="dashboard_user",
        )

        filter_group_title("3. Valores")
        min_amount = st.number_input(
            "Valor mínimo",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="dashboard_min_amount",
        )
        max_amount = st.number_input(
            "Valor máximo",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key="dashboard_max_amount",
        )

        normalized_start = _date_to_api(start_date)
        normalized_end = _date_to_api(end_date)
        normalized_min = min_amount if min_amount > 0 else None
        normalized_max = max_amount if max_amount > 0 else None

        if normalized_start and normalized_end and normalized_start > normalized_end:
            warning_box("A data inicial não pode ser maior que a data final.")
            normalized_end = None

        if (
            normalized_min is not None
            and normalized_max is not None
            and normalized_min > normalized_max
        ):
            warning_box("O valor mínimo não pode ser maior que o valor máximo.")
            normalized_max = None

        filter_group_title("Ações")
        action_refresh, action_clear = st.columns(2, gap="large")
        with action_refresh:
            refresh_clicked = primary_button("Atualizar", key="dashboard_refresh_button", icon="↻")
        with action_clear:
            clear_clicked = secondary_button("Limpar filtros", key="dashboard_clear_button", icon="×")
        if clear_clicked:
            for key in (
                "dashboard_competence",
                "dashboard_supplier",
                "dashboard_category",
                "dashboard_user",
                "dashboard_start",
                "dashboard_end",
                "dashboard_min_amount",
                "dashboard_max_amount",
            ):
                st.session_state.pop(key, None)
            st.rerun()
        if refresh_clicked:
            st.rerun()

        if secondary_button("Testar conexão", key="dashboard_connection_button", icon="✓"):
            try:
                result = testar_conexao()
                if result["status"] == "ok":
                    success_box(result["database"])
                else:
                    error_box(result["database"])
            except APIClientError as error:
                error_box(str(error))

    return {
        "competence_id": competence_options[selected_competence],
        "fornecedor": selected_supplier,
        "categoria": selected_category,
        "usuario": selected_user,
        "data_inicio": normalized_start,
        "data_fim": normalized_end,
        "valor_minimo": normalized_min,
        "valor_maximo": normalized_max,
    }


def _render_dashboard(dashboard: dict[str, Any]) -> None:
    """Renderiza abas do dashboard financeiro."""
    metrics = dashboard["metricas"]
    entries = _frame(dashboard["lancamentos"])
    suppliers = _frame(dashboard["por_fornecedor"])
    categories = _frame(dashboard["por_categoria"])
    users = _frame(dashboard["por_usuario"])
    by_day = _frame(dashboard["por_dia"])
    biggest = _frame(dashboard["maiores_despesas"])

    _render_metrics(metrics)

    tabs = st.tabs(
        [
            "VISÃO GERAL",
            "FORNECEDORES",
            "CATEGORIAS",
            "USUÁRIOS",
            "POR DIA",
            "MAIORES DESPESAS",
            "DIAGNÓSTICO",
        ],
    )

    with tabs[0]:
        _render_overview(entries, suppliers, categories, by_day)
    with tabs[1]:
        _render_rankings(
            suppliers,
            "nome",
            "Fornecedor",
            "Top 10 fornecedores",
            "supplier_ranking",
        )
    with tabs[2]:
        _render_rankings(
            categories,
            "nome",
            "Categoria",
            "Top 10 categorias",
            "category_ranking",
        )
    with tabs[3]:
        _render_users(users)
    with tabs[4]:
        _render_by_day(by_day)
    with tabs[5]:
        _render_biggest(biggest)
    with tabs[6]:
        _render_diagnostics()

    section_title(
        "Tabela detalhada dos lançamentos",
        "Registros financeiros retornados pelos filtros atuais.",
    )
    if entries.empty:
        info_box("Nenhum lançamento encontrado para os filtros selecionados.")
    else:
        render_table(
            entries,
            height=560,
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
            hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
            caption="Valores monetários e datas são formatados para leitura financeira.",
        )
    page_footer()


def _render_metrics(metrics: dict[str, Any]) -> None:
    """Renderiza cards de indicadores."""
    total = Decimal(str(metrics.get("total") or 0))
    ticket = Decimal(str(metrics.get("ticket_medio") or 0))
    biggest = Decimal(str(metrics.get("maior_despesa") or 0))

    render_metric_cards(
        [
            {"label": "Lançamentos", "value": int(metrics.get("quantidade") or 0), "icon": "Q", "description": "Registros no filtro atual"},
            {"label": "Total", "value": _format_currency(total), "icon": "R$", "description": "Soma dos lançamentos"},
            {"label": "Ticket médio", "value": _format_currency(ticket), "icon": "M", "description": "Média por lançamento"},
            {"label": "Maior despesa", "value": _format_currency(biggest), "icon": "↑", "description": "Maior valor individual"},
        ],
        columns=4,
    )


def _render_overview(
    entries: pd.DataFrame,
    suppliers: pd.DataFrame,
    categories: pd.DataFrame,
    by_day: pd.DataFrame,
) -> None:
    """Renderiza a visao geral."""
    if entries.empty:
        info_box("Nenhum dado financeiro para exibir.")
        return

    col_daily, col_category = card_grid(2)
    with col_daily:
        if not by_day.empty:
            fig = px.line(
                by_day,
                x="data",
                y="total",
                markers=True,
                color_discrete_sequence=["#3B82F6"],
                labels={"data": "DIA", "total": "TOTAL"},
            )
            _style_chart(fig, "Evolução diária", height=360)
            st.plotly_chart(fig, width="stretch", key="overview_daily_line")

    with col_category:
        if not categories.empty:
            fig = px.pie(
                categories.head(10),
                names="nome",
                values="total",
                hole=0.45,
                color_discrete_sequence=CHART_COLORS,
            )
            _style_chart(fig, "Categorias em destaque", height=360)
            st.plotly_chart(fig, width="stretch", key="overview_category_donut")

    if not suppliers.empty:
        fig = px.bar(
            suppliers.head(10),
            x="nome",
            y="total",
            color_discrete_sequence=CHART_COLORS,
            labels={"nome": "FORNECEDOR", "total": "TOTAL"},
        )
        _style_chart(fig, "Fornecedores em destaque", height=430)
        st.plotly_chart(fig, width="stretch", key="overview_supplier_bar")


def _render_rankings(
    frame: pd.DataFrame,
    label_column: str,
    label: str,
    title: str,
    key_prefix: str,
) -> None:
    """Renderiza ranking em barras e tabela."""
    section_title(title)
    if frame.empty:
        info_box("Nenhum dado encontrado para os filtros selecionados.")
        return

    top_10 = frame.head(10)
    fig = px.bar(
        top_10.sort_values("total", ascending=True),
        x="total",
        y=label_column,
        orientation="h",
        color_discrete_sequence=CHART_COLORS,
        labels={"total": "TOTAL", label_column: label.upper()},
    )
    _style_chart(fig, title)
    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_bar")
    render_table(
        frame,
        height=420,
        key=f"{key_prefix}_table",
        column_order=("nome", "total", "quantidade_lancamentos", "ticket_medio", "percentual_sobre_total"),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
    )


def _render_users(users: pd.DataFrame) -> None:
    """Renderiza gastos por usuario."""
    section_title("Gastos por usuário")
    if users.empty:
        info_box("Nenhum usuário encontrado para os filtros selecionados.")
        return

    col_bar, col_pie = card_grid(2)
    with col_bar:
        fig = px.bar(
            users,
            x="nome",
            y="total",
            color_discrete_sequence=CHART_COLORS,
            labels={"nome": "USUÁRIO", "total": "TOTAL"},
        )
        _style_chart(fig, "Gastos por usuário", height=380)
        st.plotly_chart(fig, width="stretch", key="users_bar")
    with col_pie:
        fig = px.pie(
            users,
            names="nome",
            values="total",
            hole=0.45,
            color_discrete_sequence=CHART_COLORS,
        )
        _style_chart(fig, "Participação por usuário", height=380)
        st.plotly_chart(fig, width="stretch", key="users_donut")


def _render_by_day(by_day: pd.DataFrame) -> None:
    """Renderiza linha por dia."""
    section_title("Gastos por dia")
    if by_day.empty:
        info_box("Nenhum lançamento com data para os filtros selecionados.")
        return

    fig = px.line(
        by_day,
        x="data",
        y="total",
        markers=True,
        color_discrete_sequence=["#3B82F6"],
        labels={"data": "DIA", "total": "TOTAL"},
    )
    _style_chart(fig, "Gastos por dia", height=390)
    st.plotly_chart(fig, width="stretch", key="daily_line")
    render_table(
        by_day,
        height=360,
        column_order=("data", "total", "quantidade_lancamentos", "ticket_medio"),
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
    )


def _render_biggest(biggest: pd.DataFrame) -> None:
    """Renderiza maiores despesas."""
    section_title("Maiores despesas")
    if biggest.empty:
        info_box("Nenhuma despesa encontrada para os filtros selecionados.")
        return

    chart_frame = biggest.head(10).copy()
    chart_frame["label"] = chart_frame.apply(
        lambda row: f"{row.get('fornecedor') or 'Sem fornecedor'} | "
        f"{row.get('categoria') or 'Sem categoria'}",
        axis=1,
    )
    fig = px.bar(
        chart_frame.sort_values("valor", ascending=True),
        x="valor",
        y="label",
        orientation="h",
        color_discrete_sequence=["#EF4444"],
        labels={"valor": "VALOR", "label": "DESPESA"},
    )
    _style_chart(fig, "Maiores despesas", height=430)
    st.plotly_chart(fig, width="stretch", key="biggest_expenses_bar")
    render_table(
        biggest,
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
        hidden_columns=MANAGEMENT_HIDDEN_COLUMNS,
    )


def _render_diagnostics() -> None:
    """Renderiza diagnostico da importacao mais recente ou selecionada."""
    section_title("Diagnóstico da Importação")
    try:
        imports = listar_importacoes()
        if not imports:
            info_box("Nenhuma importação registrada.")
            return

        options = {
            (
                f"{item['id_importacao']} - {item['competencia']} - "
                f"{item['arquivo_original']} - {item['status']}"
            ): int(item["id_importacao"])
            for item in imports
        }
        selected = st.selectbox(
            "Importação",
            options=list(options.keys()),
            help="Lote usado para exibir a prévia e os campos do diagnóstico.",
            key="dashboard_diagnostic_import",
        )
        diagnostics = obter_diagnostico_importacao(options[selected])
    except APIClientError as error:
        error_box(f"Não foi possível carregar diagnóstico: {error}")
        return

    render_metric_cards(
        [
            {"label": "Status", "value": str(diagnostics["status"]), "icon": "S", "description": "Situação do lote"},
            {"label": "Registros extraídos", "value": diagnostics["extracted_count"], "icon": "E", "description": "Linhas lidas"},
            {"label": "Registros gravados", "value": diagnostics["saved_count"], "icon": "G", "description": "Linhas persistidas"},
        ],
        columns=3,
    )

    col_tables, col_fields = card_grid(2)
    with col_tables:
        section_title("Tabelas identificadas")
        tables_frame = pd.DataFrame({"tabela": diagnostics.get("tables") or []})
        render_table(
            tables_frame,
            height=240,
        )
    with col_fields:
        section_title("Campos não mapeados")
        fields_frame = pd.DataFrame({"campo": diagnostics.get("unmapped_fields") or []})
        render_table(
            fields_frame,
            height=240,
        )

    section_title("Prévia dos lançamentos gravados")
    saved_preview_frame = pd.DataFrame(diagnostics.get("saved_preview") or [])
    render_table(
        saved_preview_frame,
        height=360,
    )


def _frame(data: list[dict[str, Any]]) -> pd.DataFrame:
    """Cria DataFrame e normaliza colunas monetarias."""
    frame = pd.DataFrame(data or [])
    for column in ("total", "valor"):
        if column in frame.columns:
            frame[column] = frame[column].map(lambda value: float(value or 0))
    return frame


def _format_currency(value: object) -> str:
    """Formata valores monetarios para exibicao."""
    amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _date_to_api(value: object) -> str | None:
    """Converte data do Streamlit para string de API."""
    if isinstance(value, date):
        return value.isoformat()
    return None


def _style_chart(fig: go.Figure, title: str, height: int = 390) -> None:
    """Aplica tema visual light aos graficos do dashboard."""
    fig.update_traces(marker_line_width=0, opacity=0.94)
    fig.update_layout(
        title={
            "text": title.upper(),
            "font": {"size": 14, "color": "#0F172A"},
            "x": 0,
            "xanchor": "left",
        },
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif", "size": 12, "color": "#0F172A"},
        height=height,
        margin={"l": 20, "r": 20, "t": 60, "b": 30},
        hovermode="x unified",
        hoverlabel={
            "bgcolor": "rgba(15, 23, 42, 0.94)",
            "bordercolor": "rgba(255,255,255,0.12)",
            "font": {"color": "#FFFFFF", "size": 12},
        },
        showlegend=True,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E2E8F0",
        zeroline=False,
        color="#0F172A",
        tickfont={"color": "#0F172A"},
        title_font={"size": 11},
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        color="#0F172A",
        tickfont={"color": "#0F172A"},
        title_font={"size": 11},
    )


if __name__ == "__main__":
    main()
