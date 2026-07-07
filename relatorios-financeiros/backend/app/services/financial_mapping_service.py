"""Mapeamento de registros SQL para lancamentos financeiros."""

from __future__ import annotations

import re
from typing import Any


class FinancialMappingService:
    """Centraliza aliases e normalizacao para financial_entries."""

    IGNORED_SOURCE_TABLES: set[str] = {"categorias", "fornecedores", "usuarios"}

    FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "entry_date": (
            "entry_date",
            "data_lancamento",
            "lancamento",
            "data",
            "data_documento",
            "dt_lancamento",
            "lancamento_data",
        ),
        "payment_date": (
            "payment_date",
            "data_pagamento",
            "data_credito",
            "data",
            "dt_pagamento",
            "pagamento_data",
        ),
        "created_at_source": (
            "created_at_source",
            "created_at",
            "criado_em",
            "data_criacao",
            "dt_criacao",
            "exec_baixa",
        ),
        "document_number": (
            "document_number",
            "documento",
            "numero_documento",
            "num_documento",
            "numero",
            "nota_fiscal",
            "nf",
            "recibo",
            "nosso_numero",
            "cartao_num_doc",
        ),
        "transaction_type": (
            "transaction_type",
            "tipo",
            "tipo_lancamento",
            "tipo_transacao",
            "operacao",
            "historico",
        ),
        "category": (
            "category",
            "categoria",
            "categoria_id",
            "classificador",
            "grupo",
            "classificacao",
        ),
        "service": (
            "service",
            "servico",
            "serviço",
            "historico",
            "histórico",
            "descricao",
            "descrição",
        ),
        "supplier": (
            "supplier",
            "fornecedor",
            "fornecedor_id",
            "prestador",
            "credor",
            "favorecido",
            "nome",
        ),
        "supplier_type": (
            "supplier_type",
            "tipo_fornecedor",
            "fornecedor_tipo",
            "tipo_pessoa",
            "tipo_doc",
        ),
        "city": ("city", "cidade", "municipio", "município", "cidade_inferida"),
        "cost_center": (
            "cost_center",
            "centro_custo",
            "centro_de_custo",
            "ccusto",
        ),
        "description": (
            "description",
            "descricao",
            "descrição",
            "historico",
            "histórico",
            "observacao",
            "observação",
            "classificador",
        ),
        "amount": (
            "amount",
            "valor",
            "valor_total",
            "vl_total",
            "total",
            "preco",
            "preço",
        ),
        "user_name": (
            "user_name",
            "usuario",
            "usuário",
            "usuario_id",
            "nome_usuario",
            "usuarios",
        ),
    }

    EMPTY_STRINGS: set[str] = {"", "none", "null", "nan"}

    def map_record(
        self,
        record: dict[str, Any],
        lookup_context: dict[str, dict[str, dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Aplica aliases de colunas conhecidas ao registro extraido."""
        source_table = str(record.get("_source_table", "")).lower()
        if source_table in self.IGNORED_SOURCE_TABLES:
            return {}

        normalized_record = {
            self.normalize_key(key): value
            for key, value in record.items()
            if not key.startswith("_")
        }
        mapped: dict[str, Any] = {}

        for target_field, aliases in self.FIELD_ALIASES.items():
            for alias in aliases:
                value = self._get_normalized_value(
                    normalized_record,
                    self.normalize_key(alias),
                )
                if value is not None:
                    mapped[target_field] = value
                    break

        if lookup_context:
            self._apply_lookup_fields(mapped, normalized_record, lookup_context)

        if not mapped:
            return {}

        if "amount" not in mapped:
            mapped["amount"] = 0

        return mapped

    def build_lookup_context(
        self,
        records: list[dict[str, Any]],
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Cria mapas de lookup para SQLs normalizados por tabelas auxiliares."""
        lookups: dict[str, dict[str, dict[str, Any]]] = {
            "categorias": {},
            "fornecedores": {},
            "usuarios": {},
        }

        for record in records:
            source_table = str(record.get("_source_table", "")).lower()
            if source_table not in lookups:
                continue

            normalized = {
                self.normalize_key(key): value
                for key, value in record.items()
                if not key.startswith("_")
            }
            record_id = normalized.get("id")
            if record_id in (None, ""):
                continue

            lookups[source_table][str(record_id)] = normalized

        return lookups

    def get_unmapped_fields(self, records: list[dict[str, Any]]) -> list[str]:
        """Lista campos extraidos que nao possuem alias para financial_entries."""
        mapped_aliases = {
            self.normalize_key(alias)
            for aliases in self.FIELD_ALIASES.values()
            for alias in aliases
        }
        extracted_fields = {
            self.normalize_key(key)
            for record in records
            for key in record
            if not key.startswith("_")
        }
        return sorted(extracted_fields - mapped_aliases)

    def normalize_text(self, value: Any) -> str | None:
        """Normaliza texto preservando acentos e sem forcar caixa alta."""
        if value is None:
            return None

        normalized = re.sub(r"\s+", " ", str(value).strip())
        if normalized.lower() in self.EMPTY_STRINGS:
            return None

        return normalized

    @staticmethod
    def normalize_key(value: str) -> str:
        """Normaliza nome de coluna para comparacao por aliases."""
        normalized = value.strip().lower()
        normalized = normalized.replace("ç", "c").replace("ã", "a")
        normalized = normalized.replace("á", "a").replace("à", "a")
        normalized = normalized.replace("â", "a").replace("é", "e")
        normalized = normalized.replace("ê", "e").replace("í", "i")
        normalized = normalized.replace("ó", "o").replace("ô", "o")
        normalized = normalized.replace("õ", "o").replace("ú", "u")
        return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")

    def _apply_lookup_fields(
        self,
        mapped: dict[str, Any],
        normalized_record: dict[str, Any],
        lookup_context: dict[str, dict[str, dict[str, Any]]],
    ) -> None:
        """Resolve IDs de tabelas auxiliares para nomes consolidados."""
        category_id = normalized_record.get("categoria_id")
        if category_id not in (None, ""):
            category = lookup_context["categorias"].get(str(category_id))
            if category:
                mapped["category"] = self.normalize_text(category.get("nome"))
                mapped.setdefault(
                    "city",
                    self.normalize_text(category.get("cidade_inferida")),
                )

        supplier_id = normalized_record.get("fornecedor_id")
        if supplier_id not in (None, ""):
            supplier = lookup_context["fornecedores"].get(str(supplier_id))
            if supplier:
                mapped["supplier"] = self.normalize_text(supplier.get("nome"))
                mapped["supplier_type"] = self.normalize_text(supplier.get("tipo_doc"))

        user_id = normalized_record.get("usuario_id")
        if user_id not in (None, ""):
            user = lookup_context["usuarios"].get(str(user_id))
            if user:
                mapped["user_name"] = self.normalize_text(user.get("nome"))

        city = self.normalize_text(normalized_record.get("cidade_inferida"))
        if city is not None:
            mapped["city"] = city

    def _get_normalized_value(
        self,
        normalized_record: dict[str, Any],
        normalized_alias: str,
    ) -> Any | None:
        value = normalized_record.get(normalized_alias)
        if isinstance(value, str):
            return self.normalize_text(value)
        return value
