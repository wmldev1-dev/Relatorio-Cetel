"""Componentes de graficos Plotly do frontend."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
CYAN = "#06B6D4"
GREEN = "#16A34A"
RED = "#DC2626"
YELLOW = "#F59E0B"
MUTED = "#64748B"
GRID = "#E2E8F0"
PALETTE = [BLUE, CYAN, "#8B5CF6", YELLOW, GREEN, RED]


def comparison_bar_chart(
    competencia_base: str,
    total_base: object,
    competencia_comparacao: str,
    total_comparacao: object,
) -> None:
    """Grafico de ponte para comparar total base, variacao e total final."""
    base = _to_float(total_base)
    comparison = _to_float(total_comparacao)
    difference = comparison - base
    difference_color = RED if difference > 0 else GREEN if difference < 0 else MUTED

    fig = go.Figure(
        go.Waterfall(
            name="Comparativo",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=[
                competencia_base,
                "Variação",
                competencia_comparacao,
            ],
            y=[
                base,
                difference,
                comparison,
            ],
            text=[
                _format_brl(base),
                _format_brl(difference),
                _format_brl(comparison),
            ],
            textposition="outside",
            connector={"line": {"color": "#CBD5E1", "width": 1}},
            increasing={"marker": {"color": RED}},
            decreasing={"marker": {"color": GREEN}},
            totals={"marker": {"color": BLUE}},
            hovertemplate="<b>%{x}</b><br>Valor: %{text}<extra></extra>",
        ),
    )
    _apply_layout(fig, "Resumo da variação mensal", height=430)
    fig.update_yaxes(tickprefix="R$ ", separatethousands=True)
    fig.add_annotation(
        x="Variação",
        y=difference,
        text="AUMENTO" if difference > 0 else "REDUÇÃO" if difference < 0 else "ESTÁVEL",
        showarrow=False,
        yshift=28 if difference >= 0 else -28,
        font={"color": difference_color, "size": 11},
        bgcolor="#FFFFFF",
        bordercolor=GRID,
        borderpad=4,
    )
    _render_chart(fig)


def comparison_grouped_bar_chart(
    competencia_base: str,
    total_base: object,
    competencia_comparacao: str,
    total_comparacao: object,
) -> None:
    """Grafico de barras comparando totais mensais."""
    frame = pd.DataFrame(
        [
            {"competencia": competencia_base, "total": _to_float(total_base)},
            {"competencia": competencia_comparacao, "total": _to_float(total_comparacao)},
        ],
    )
    fig = px.bar(
        frame,
        x="competencia",
        y="total",
        text="total",
        color="competencia",
        color_discrete_sequence=[BLUE, CYAN],
        labels={"competencia": "COMPETÊNCIA", "total": "TOTAL"},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
    )
    _apply_layout(fig, "Total por competência")
    _render_chart(fig)


def ranking_horizontal_bar_chart(
    rows: list[dict[str, Any]],
    title: str,
    value_column: str = "diferenca_valor",
) -> None:
    """Ranking horizontal por diferenca de valor."""
    if not rows:
        empty_chart_state("Sem dados para o gráfico.")
        return
    frame = pd.DataFrame(rows).copy().head(10)
    frame[value_column] = frame[value_column].map(_to_float)
    frame = frame.sort_values(value_column, ascending=True)
    color = RED if frame[value_column].max() > 0 else GREEN
    fig = px.bar(
        frame,
        x=value_column,
        y="nome",
        orientation="h",
        text=value_column,
        color_discrete_sequence=[color],
        labels={value_column: "VALOR", "nome": ""},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>",
    )
    fig.add_vline(x=0, line_width=1, line_dash="dot", line_color=MUTED)
    _apply_layout(fig, title, height=max(330, 140 + len(frame) * 34))
    _render_chart(fig)


def supplier_total_ranking_chart(rows: list[dict[str, Any]]) -> None:
    total_ranking_chart(rows, "fornecedor", "Ranking por total gasto")


def supplier_share_chart(rows: list[dict[str, Any]]) -> None:
    donut_chart(rows, "fornecedor", "percentual_sobre_total", "Participação por fornecedor")


def service_total_ranking_chart(rows: list[dict[str, Any]]) -> None:
    total_ranking_chart(rows, "servico", "Ranking por total gasto")


def service_share_chart(rows: list[dict[str, Any]]) -> None:
    donut_chart(rows, "servico", "percentual_sobre_total", "Participação por serviço")


def total_ranking_chart(rows: list[dict[str, Any]], label_column: str, title: str) -> None:
    """Ranking horizontal por total."""
    if not rows:
        empty_chart_state("Sem dados para o gráfico.")
        return
    frame = pd.DataFrame(rows).copy()
    frame["total"] = frame["total"].map(_to_float)
    frame = frame.sort_values("total", ascending=True).tail(10)
    fig = px.bar(
        frame,
        x="total",
        y=label_column,
        orientation="h",
        text="total",
        color_discrete_sequence=[BLUE],
        labels={"total": "VALOR TOTAL", label_column: ""},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Total: R$ %{x:,.2f}<extra></extra>",
    )
    _apply_layout(fig, title, height=max(360, 150 + len(frame) * 34))
    _render_chart(fig)


def donut_chart(
    rows: list[dict[str, Any]],
    label_column: str,
    value_column: str,
    title: str,
) -> None:
    """Grafico donut de participacao."""
    if not rows:
        empty_chart_state("Sem dados para o gráfico.")
        return
    frame = pd.DataFrame(rows).copy().head(10)
    frame[value_column] = frame[value_column].map(_to_float)
    fig = px.pie(
        frame,
        names=label_column,
        values=value_column,
        hole=0.55,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Participação: %{value:.2f}%<extra></extra>",
    )
    _apply_layout(fig, title, height=380)
    fig.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.12})
    _render_chart(fig)


def monthly_evolution_chart(rows: list[dict[str, Any]], title: str = "Evolução mensal") -> None:
    """Linha de evolucao mensal."""
    if not rows:
        empty_chart_state("Sem dados para o gráfico.")
        return
    frame = pd.DataFrame(rows).copy()
    fig = px.line(frame, x="mes", y="total", markers=True, color_discrete_sequence=[BLUE])
    _apply_layout(fig, title)
    _render_chart(fig)


def executive_monthly_line(rows: list[dict[str, Any]]) -> None:
    """Linha de evolucao mensal para o dashboard executivo."""
    if not rows:
        empty_chart_state("Sem dados para evolução mensal.")
        return
    frame = pd.DataFrame(rows).copy()
    frame["total"] = frame["total"].map(_to_float)
    fig = px.line(
        frame,
        x="competencia",
        y="total",
        markers=True,
        text="total",
        color_discrete_sequence=[BLUE],
        labels={"competencia": "COMPETÊNCIA", "total": "TOTAL"},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="top center",
        hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
    )
    _apply_layout(fig, "Evolução mensal", height=390)
    _render_chart(fig)


def executive_horizontal_bar(
    rows: list[dict[str, Any]],
    label_column: str,
    title: str,
    color: str = BLUE,
) -> None:
    """Barra horizontal executiva ordenada por valor total."""
    if not rows:
        empty_chart_state("Sem dados para o ranking.")
        return
    frame = pd.DataFrame(rows).copy().head(10)
    frame["valor_total"] = frame["valor_total"].map(_to_float)
    frame = frame.sort_values("valor_total", ascending=True)
    fig = px.bar(
        frame,
        x="valor_total",
        y=label_column,
        orientation="h",
        text="valor_total",
        color_discrete_sequence=[color],
        labels={"valor_total": "VALOR TOTAL", label_column: ""},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Total: R$ %{x:,.2f}<extra></extra>",
    )
    _apply_layout(fig, title, height=max(360, 150 + len(frame) * 32))
    _render_chart(fig)


def executive_donut(
    rows: list[dict[str, Any]],
    label_column: str,
    title: str,
) -> None:
    """Donut executivo por percentual sobre total."""
    if not rows:
        empty_chart_state("Sem dados para distribuição.")
        return
    frame = pd.DataFrame(rows).copy().head(10)
    frame["valor_total"] = frame["valor_total"].map(_to_float)
    fig = px.pie(
        frame,
        names=label_column,
        values="valor_total",
        hole=0.58,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<extra></extra>",
    )
    _apply_layout(fig, title, height=360)
    fig.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.18})
    _render_chart(fig)


def executive_comparison_columns(rows: list[dict[str, Any]]) -> None:
    """Colunas comparando competencia atual e anterior."""
    if not rows:
        empty_chart_state("Sem dados para comparação mensal.")
        return
    frame = pd.DataFrame(rows).copy()
    frame["total"] = frame["total"].map(_to_float)
    fig = px.bar(
        frame,
        x="competencia",
        y="total",
        text="total",
        color="competencia",
        color_discrete_sequence=[CYAN, BLUE],
        labels={"competencia": "COMPETÊNCIA", "total": "TOTAL"},
    )
    fig.update_traces(
        texttemplate="R$ %{text:,.2f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
    )
    _apply_layout(fig, "Comparação mensal", height=360)
    _render_chart(fig)


def executive_city_bar(rows: list[dict[str, Any]]) -> None:
    """Distribuicao por cidade em barras."""
    executive_horizontal_bar(rows, "cidade", "Distribuição por cidade", CYAN)


def empty_chart_state(message: str = "Nenhum dado disponível.") -> None:
    with st.container(border=True):
        st.info(message)


def _render_chart(fig: go.Figure) -> None:
    """Renderiza graficos em um card visual padronizado."""
    st.markdown('<div class="rf-chart-card">', unsafe_allow_html=True)
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


def _apply_layout(fig: go.Figure, title: str, height: int = 380) -> None:
    fig.update_layout(
        title={"text": title.upper(), "font": {"size": 14, "color": "#0F172A"}},
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif", "color": "#0F172A", "size": 12},
        height=height,
        margin={"l": 18, "r": 18, "t": 54, "b": 28},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#0F172A", "font": {"color": "#FFFFFF"}},
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, title_font={"size": 11})
    fig.update_yaxes(showgrid=False, zeroline=False, title_font={"size": 11})


def _to_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(Decimal(str(value)))


def _format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
