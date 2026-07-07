"""Parser flexivel para arquivos SQL de importacao."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class SQLParserService:
    """Extrai registros de comandos INSERT em arquivos SQL."""

    _INSERT_PATTERN = re.compile(
        r"INSERT\s+INTO\s+(`?[\w.]+`?)\s*(?:\((.*?)\))?\s*VALUES\s*(.*)",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self) -> None:
        """Inicializa o parser com estado de diagnostico vazio."""
        self._last_records: list[dict[str, Any]] = []
        self._last_insert_count = 0
        self._last_tables: set[str] = set()
        self._last_columns: set[str] = set()

    def parse_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Le um arquivo SQL e retorna registros extraidos dos INSERTs."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.parse_content(content)

    def parse_content(self, content: str) -> list[dict[str, Any]]:
        """Extrai registros de todos os comandos INSERT encontrados."""
        records: list[dict[str, Any]] = []
        insert_count = 0
        tables: set[str] = set()
        columns: set[str] = set()

        for statement in self._split_statements(content):
            parsed_records = self._parse_insert_statement(statement)
            if parsed_records:
                insert_count += 1
                tables.update(
                    str(record["_source_table"])
                    for record in parsed_records
                    if "_source_table" in record
                )
                columns.update(
                    key
                    for record in parsed_records
                    for key in record
                    if not key.startswith("_")
                )

            records.extend(parsed_records)

        self._last_records = records
        self._last_insert_count = insert_count
        self._last_tables = tables
        self._last_columns = columns
        return records

    def get_parse_summary(self) -> dict[str, object]:
        """Retorna resumo da ultima execucao do parser."""
        return {
            "insert_count": self._last_insert_count,
            "record_count": len(self._last_records),
            "tables": sorted(self._last_tables),
            "columns": sorted(self._last_columns),
        }

    def preview_records(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retorna uma amostra dos registros extraidos no ultimo parse."""
        return self._last_records[:limit]

    def _parse_insert_statement(self, statement: str) -> list[dict[str, Any]]:
        """Extrai registros de um comando INSERT individual."""
        match = self._INSERT_PATTERN.match(statement.strip())
        if match is None:
            return []

        table_name = self._clean_identifier(match.group(1))
        columns = self._parse_columns(match.group(2))
        values_section = match.group(3).strip()
        rows = self._parse_values(values_section)

        records: list[dict[str, Any]] = []
        for row in rows:
            if columns:
                record = {
                    columns[index]: value
                    for index, value in enumerate(row)
                    if index < len(columns)
                }
            else:
                record = {
                    f"column_{index + 1}": value
                    for index, value in enumerate(row)
                }

            record["_source_table"] = table_name
            records.append(record)

        return records

    def _split_statements(self, content: str) -> list[str]:
        """Divide o SQL em comandos respeitando strings."""
        statements: list[str] = []
        current: list[str] = []
        quote: str | None = None
        escaped = False

        for char in content:
            current.append(char)

            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue

            if char in {"'", '"'}:
                quote = char
                continue

            if char == ";":
                statement = "".join(current).strip().rstrip(";").strip()
                if statement:
                    statements.append(statement)
                current = []

        trailing = "".join(current).strip()
        if trailing:
            statements.append(trailing)

        return statements

    def _parse_columns(self, columns_section: str | None) -> list[str]:
        """Extrai a lista de colunas de um INSERT."""
        if not columns_section:
            return []

        return [
            self._clean_identifier(column)
            for column in self._split_csv(columns_section)
        ]

    def _parse_values(self, values_section: str) -> list[list[Any]]:
        """Extrai tuplas de valores da secao VALUES."""
        rows: list[list[Any]] = []
        index = 0

        while index < len(values_section):
            char = values_section[index]
            if char != "(":
                index += 1
                continue

            row_content, index = self._read_parenthesized(values_section, index)
            values = [
                self._parse_literal(value)
                for value in self._split_csv(row_content)
            ]
            rows.append(values)

        return rows

    def _read_parenthesized(self, content: str, start: int) -> tuple[str, int]:
        """Le o conteudo dentro de parenteses respeitando strings."""
        depth = 0
        quote: str | None = None
        escaped = False
        chars: list[str] = []

        for index in range(start, len(content)):
            char = content[index]

            if quote:
                chars.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue

            if char in {"'", '"'}:
                quote = char
                chars.append(char)
                continue

            if char == "(":
                depth += 1
                if depth > 1:
                    chars.append(char)
                continue

            if char == ")":
                depth -= 1
                if depth == 0:
                    return "".join(chars), index + 1
                chars.append(char)
                continue

            chars.append(char)

        raise ValueError("Tupla de valores SQL sem fechamento de parênteses.")

    def _split_csv(self, content: str) -> list[str]:
        """Divide texto separado por virgulas respeitando strings."""
        values: list[str] = []
        current: list[str] = []
        quote: str | None = None
        escaped = False
        depth = 0

        for char in content:
            if quote:
                current.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue

            if char in {"'", '"'}:
                quote = char
                current.append(char)
                continue

            if char == "(":
                depth += 1
                current.append(char)
                continue

            if char == ")":
                depth -= 1
                current.append(char)
                continue

            if char == "," and depth == 0:
                values.append("".join(current).strip())
                current = []
                continue

            current.append(char)

        if current:
            values.append("".join(current).strip())

        return values

    def _parse_literal(self, raw_value: str) -> Any:
        """Converte literais SQL simples em valores Python."""
        value = raw_value.strip()
        upper_value = value.upper()

        if upper_value == "NULL":
            return None

        if upper_value in {"TRUE", "FALSE"}:
            return upper_value == "TRUE"

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            return self._unquote(value)

        return value

    @staticmethod
    def _clean_identifier(identifier: str) -> str:
        """Normaliza identificadores de tabela e coluna."""
        return identifier.strip().strip("`").split(".")[-1].strip("`").lower()

    @staticmethod
    def _unquote(value: str) -> str:
        """Remove aspas e escapes comuns de uma string SQL."""
        unquoted = value[1:-1]
        return (
            unquoted.replace("\\'", "'")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )
