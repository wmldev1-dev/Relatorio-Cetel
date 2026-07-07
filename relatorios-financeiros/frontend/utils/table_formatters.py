"""Utilitarios de apresentacao para tabelas do Streamlit."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st

EMPTY_TEXT_VALUES = {"", "none", "null", "nan"}

COLUMN_LABELS_PTBR = {
    "id": "ID",
    "competence": "Competência",
    "competence_id": "Competência",
    "competencia": "Competência",
    "import_batch_id": "Lote de Importação",
    "id_importacao": "ID",
    "entry_date": "Data do Lançamento",
    "data_lancamento": "Data do Lançamento",
    "payment_date": "Data de Pagamento",
    "data_pagamento": "Data de Pagamento",
    "created_at_source": "Criado na Origem",
    "created_at": "Criado em",
    "updated_at": "Atualizado em",
    "document_number": "Documento",
    "documento": "Documento",
    "transaction_type": "Tipo",
    "tipo": "Tipo",
    "category": "Categoria",
    "categoria": "Categoria",
    "service": "Serviço",
    "servico": "Serviço",
    "supplier": "Fornecedor",
    "fornecedor": "Fornecedor",
    "supplier_type": "Tipo de Fornecedor",
    "city": "Cidade",
    "cost_center": "Centro de Custo",
    "description": "Descrição",
    "descricao": "Descrição",
    "amount": "Valor",
    "valor": "Valor",
    "total": "Valor Total",
    "total_amount": "Valor Total",
    "valor_base": "Valor Base",
    "valor_comparacao": "Valor Comparação",
    "diferenca_valor": "Diferença em R$",
    "diferenca_percentual": "Variação %",
    "percentual_sobre_total": "% sobre Total",
    "percentual_preenchido": "% Preenchido",
    "quantidade_lancamentos": "Quantidade de Lançamentos",
    "quantidade_preenchida": "Quantidade Preenchida",
    "quantidade_vazia": "Quantidade Vazia",
    "ticket_medio": "Ticket Médio",
    "maior_lancamento": "Maior Lançamento",
    "menor_lancamento": "Menor Lançamento",
    "user_name": "Usuário",
    "usuario": "Usuário",
    "source_file": "Arquivo de Origem",
    "arquivo_origem": "Arquivo de Origem",
    "arquivo_original": "Arquivo",
    "arquivo_salvo": "Arquivo Salvo",
    "file_name": "Arquivo",
    "file_path": "Caminho do Arquivo",
    "caminho_arquivo": "Caminho do Arquivo",
    "status": "Status",
    "error_message": "Mensagem de Erro",
    "mensagem_erro": "Mensagem de Erro",
    "records_count": "Registros",
    "month": "Mês",
    "nome": "Nome",
    "campo": "Campo",
    "campo_nao_mapeado": "Campo não Mapeado",
    "campo_candidato": "Campo Candidato",
    "tabela": "Tabela",
    "tabela_origem": "Tabela de Origem",
    "coluna": "Coluna",
    "data": "Data",
}

CURRENCY_KEYS = (
    "valor",
    "total",
    "amount",
    "ticket",
    "maior",
    "menor",
    "diferenca_valor",
)
PERCENT_KEYS = ("percentual", "variação", "variacao", "%", "diferenca_percentual")
DATE_KEYS = ("data", "date", "criado", "created", "updated", "atualizado")
COUNT_KEYS = ("quantidade", "registros", "lançamentos", "lancamentos", "id")


def shape_table(
    df: pd.DataFrame,
    preferred_columns: list[str] | tuple[str, ...] | None = None,
    hidden_columns: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Ordena e oculta colunas para leitura, preservando os valores originais."""
    if df.empty:
        return df.copy()

    hidden = {_normalize(column) for column in hidden_columns or ()}
    visible_columns = [
        column for column in df.columns
        if _normalize(str(column)) not in hidden
    ]
    preferred = [
        column for column in preferred_columns or ()
        if column in visible_columns
    ]
    remaining = [
        column for column in visible_columns
        if column not in preferred
    ]
    return df.loc[:, [*preferred, *remaining]].copy()


def remove_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas totalmente vazias."""
    if df.empty:
        return df.copy()
    frame = df.copy()
    empty_columns = [
        column for column in frame.columns if frame[column].map(_is_empty_value).all()
    ]
    return frame.drop(columns=empty_columns)


def rename_columns_ptbr(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas e deixa apenas cabecalhos em caixa alta."""
    renamed = df.rename(columns=COLUMN_LABELS_PTBR)
    return renamed.rename(columns={column: str(column).upper() for column in renamed.columns})


def prepare_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara dados para exibicao sem alterar caixa dos valores textuais."""
    frame = remove_empty_columns(df)
    frame = frame.map(lambda value: "" if _is_empty_value(value) else value)
    frame = _format_display_values(frame)
    return rename_columns_ptbr(frame)


def build_column_config(df: pd.DataFrame) -> dict[str, Any]:
    """Cria configuracao de colunas para st.dataframe."""
    config: dict[str, Any] = {}
    for column in df.columns:
        normalized = _normalize(str(column))
        if any(key in normalized for key in ("fornecedor", "serviço", "servico", "nome")):
            config[column] = st.column_config.TextColumn(column, width="medium")
        elif _matches(normalized, CURRENCY_KEYS):
            config[column] = st.column_config.TextColumn(column, width="small")
        elif _matches(normalized, PERCENT_KEYS):
            config[column] = st.column_config.TextColumn(column, width="small")
        elif _matches(normalized, DATE_KEYS):
            config[column] = st.column_config.TextColumn(column, width="small")
        elif _matches(normalized, COUNT_KEYS):
            config[column] = st.column_config.TextColumn(column, width="small")
        elif any(key in normalized for key in ("descrição", "descricao", "mensagem", "caminho", "arquivo")):
            config[column] = st.column_config.TextColumn(column, width="large")
        else:
            config[column] = st.column_config.TextColumn(column, width="medium")
    return config


def _format_display_values(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    for column in frame.columns:
        normalized = _normalize(str(column))
        if _matches(normalized, CURRENCY_KEYS):
            frame[column] = frame[column].map(_format_currency)
        elif _matches(normalized, PERCENT_KEYS):
            frame[column] = frame[column].map(_format_percent)
        elif _matches(normalized, DATE_KEYS):
            frame[column] = _format_date_series(frame[column])
        elif _matches(normalized, COUNT_KEYS):
            frame[column] = frame[column].map(_format_integer)
    return frame


def _format_date_series(series: pd.Series) -> pd.Series:
    dates = pd.to_datetime(series, errors="coerce")
    formatted = dates.dt.strftime("%d/%m/%Y")
    return formatted.where(dates.notna(), series)


def _is_empty_value(value: object) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_TEXT_VALUES
    return False


def _format_currency(value: object) -> str:
    if _is_empty_value(value):
        return ""
    text = str(value)
    if text.startswith("R$"):
        return text
    try:
        amount = value if isinstance(value, Decimal) else Decimal(text)
    except (InvalidOperation, ValueError):
        return text
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_percent(value: object) -> str:
    if _is_empty_value(value):
        return ""
    text = str(value)
    if text.endswith("%"):
        return text
    try:
        amount = value if isinstance(value, Decimal) else Decimal(text)
    except (InvalidOperation, ValueError):
        return text
    return f"{amount:.2f}%".replace(".", ",")


def _format_integer(value: object) -> str:
    if _is_empty_value(value):
        return ""
    try:
        return str(int(Decimal(str(value))))
    except (InvalidOperation, ValueError):
        return str(value)


def _normalize(value: str) -> str:
    return value.strip().lower()


def _matches(value: str, keys: tuple[str, ...]) -> bool:
    return any(key in value for key in keys)
