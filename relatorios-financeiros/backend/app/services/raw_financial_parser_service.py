"""Parser para relatorios financeiros brutos em texto tabulado."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class RawFinancialParserService:
    """Converte arquivos brutos exportados para registros normalizados."""

    COLUMN_ALIASES: dict[str, str] = {
        "lancamento": "lancamento",
        "data": "data_documento",
        "recibo": "recibo",
        "baixa": "baixa",
        "data_credito": "data_credito",
        "cartao_num_doc": "cartao_num_doc",
        "cartao_cod_aut": "cartao_cod_aut",
        "exec_de_baixa": "exec_baixa",
        "numero": "numero",
        "nosso_numero": "nosso_numero",
        "historico": "historico",
        "classificador": "classificador",
        "nome": "nome",
        "tipo_doc": "tipo_doc",
        "banco": "banco",
        "valor": "valor",
        "usuarios": "usuarios",
    }

    def __init__(self) -> None:
        """Inicializa o parser com diagnostico vazio."""
        self._last_records: list[dict[str, Any]] = []
        self._last_columns: list[str] = []

    def parse_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Le arquivo bruto e retorna registros extraidos."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.parse_content(content)

    def parse_content(self, content: str) -> list[dict[str, Any]]:
        """Converte conteudo bruto em lista de dicionarios normalizados."""
        lines = [line.rstrip("\r") for line in content.splitlines()]
        columns, data_start = self._extract_columns(lines)
        if not columns:
            self._last_records = []
            self._last_columns = []
            return []

        records: list[dict[str, Any]] = []
        pending_record: dict[str, Any] | None = None
        for line in lines[data_start:]:
            if not line.strip() or self._is_section_marker(line):
                continue

            if self._is_financial_row(line):
                if pending_record is not None:
                    records.append(pending_record)
                pending_record = self._parse_financial_row(line)
                continue

            user_name = self._extract_user_name(line)
            if pending_record is not None and user_name:
                pending_record["usuarios"] = user_name
                records.append(pending_record)
                pending_record = None
                continue

            values = self._split_row(line)
            if len(values) < len(columns):
                continue
            if len(values) > len(columns):
                values = values[: len(columns) - 1] + [
                    "\t".join(values[len(columns) - 1:]),
                ]

            record = {
                columns[index]: self._normalize_value(columns[index], value)
                for index, value in enumerate(values)
            }
            record["_source_table"] = "lancamentos"
            records.append(record)

        if pending_record is not None:
            records.append(pending_record)

        self._last_records = records
        self._last_columns = columns
        return records

    def get_parse_summary(self) -> dict[str, object]:
        """Retorna resumo da ultima leitura."""
        return {
            "insert_count": 0,
            "record_count": len(self._last_records),
            "tables": ["lancamentos"] if self._last_records else [],
            "columns": sorted(self._last_columns),
        }

    def preview_records(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retorna amostra dos registros brutos normalizados."""
        return self._last_records[:limit]

    def _extract_columns(self, lines: list[str]) -> tuple[list[str], int]:
        columns: list[str] = []
        in_columns = False
        data_start = 0

        for index, line in enumerate(lines):
            normalized = self._normalize_key(line)
            if normalized == "colunas":
                in_columns = True
                continue

            if not in_columns:
                continue

            if normalized in {"linhas", "registros", "dados"}:
                data_start = index + 1
                break

            if not line.strip():
                continue

            if "\t" in line and len(columns) >= 3:
                data_start = index
                break

            columns.append(self.COLUMN_ALIASES.get(normalized, normalized))

        if data_start == 0:
            data_start = len(lines)

        return columns, data_start

    def _split_row(self, line: str) -> list[str]:
        if "\t" in line:
            return [value.strip() for value in line.split("\t")]
        return [value.strip() for value in re.split(r"\s{2,}", line.strip())]

    def _is_financial_row(self, line: str) -> bool:
        return "R$" in line and bool(re.search(r"\d{2}/\d{2}/\d{4}", line))

    def _parse_financial_row(self, line: str) -> dict[str, Any]:
        values = self._trim_to_first_date(self._split_row(line))
        non_empty = [value for value in values if value.strip()]
        date_values = [
            value for value in non_empty
            if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value)
        ]
        datetime_value = next(
            (
                value for value in non_empty
                if re.fullmatch(r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}", value)
            ),
            None,
        )
        amount_index = next(
            index for index, value in enumerate(values)
            if "R$" in value
        )
        datetime_index = (
            values.index(datetime_value)
            if datetime_value in values
            else -1
        )

        details = [
            value for value in values[datetime_index + 3:amount_index]
            if value.strip()
        ]

        return {
            "lancamento": date_values[0] if date_values else None,
            "data_documento": date_values[1] if len(date_values) > 1 else None,
            "recibo": self._value_at(values, 2),
            "baixa": self._value_at(values, 3),
            "data_credito": date_values[-1] if date_values else None,
            "cartao_num_doc": None,
            "cartao_cod_aut": None,
            "exec_baixa": datetime_value,
            "numero": self._value_at(values, datetime_index + 1),
            "nosso_numero": self._value_at(values, datetime_index + 2),
            "historico": self._value_at(details, 0),
            "classificador": self._value_at(details, 1),
            "nome": self._value_at(details, 2),
            "tipo_doc": self._value_at(details, 3),
            "banco": self._value_at(details, 4),
            "valor": self._normalize_amount(values[amount_index]),
            "usuarios": self._value_at(values, amount_index + 1),
            "_source_table": "lancamentos",
        }

    def _extract_user_name(self, line: str) -> str | None:
        values = [value for value in self._split_row(line) if value.strip()]
        if len(values) == 1 and not re.search(r"\d{2}/\d{2}/\d{4}|R\$", values[0]):
            return values[0]
        return None

    def _trim_to_first_date(self, values: list[str]) -> list[str]:
        for index, value in enumerate(values):
            if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value.strip()):
                return values[index:]
        return values

    def _value_at(self, values: list[str], index: int) -> str | None:
        if index < 0 or index >= len(values):
            return None
        return self.normalize_text(values[index])

    def _normalize_value(self, column: str, value: str) -> Any:
        normalized = self.normalize_text(value)
        if normalized is None:
            return None

        if column == "valor":
            return self._normalize_amount(normalized)

        return normalized

    def normalize_text(self, value: str) -> str | None:
        """Normaliza textos vazios do arquivo bruto."""
        normalized = re.sub(r"\s+", " ", value.strip())
        if normalized.lower() in {"", "none", "null", "nan"}:
            return None
        return normalized

    def _normalize_amount(self, value: str) -> str:
        normalized = value.replace("R$", "").replace("\xa0", " ").strip()
        normalized = normalized.replace(".", "").replace(",", ".")
        normalized = re.sub(r"[^0-9.-]", "", normalized)
        try:
            return str(Decimal(normalized).quantize(Decimal("0.01")))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"Valor financeiro inválido no arquivo bruto: {value}") from error

    def _is_section_marker(self, line: str) -> bool:
        return self._normalize_key(line) in {"colunas", "linhas", "registros", "dados"}

    @staticmethod
    def _normalize_key(value: str) -> str:
        normalized = value.strip().lower().rstrip(":")
        normalized = normalized.replace("ç", "c").replace("ã", "a")
        normalized = normalized.replace("á", "a").replace("à", "a")
        normalized = normalized.replace("â", "a").replace("é", "e")
        normalized = normalized.replace("ê", "e").replace("í", "i")
        normalized = normalized.replace("ó", "o").replace("ô", "o")
        normalized = normalized.replace("õ", "o").replace("ú", "u")
        return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
