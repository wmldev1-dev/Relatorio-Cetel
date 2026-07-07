"""Schemas de importacoes."""

from __future__ import annotations

from app.schemas.common import APIModel


class ImportacaoResponse(APIModel):
    """Importacao registrada."""

    competencia: str
    id_importacao: str
    arquivo_original: str
    arquivo_salvo: str
    status: str
    data_importacao: str
    erro: str


class ImportacaoCreateResponse(APIModel):
    """Resultado do registro de importacao."""

    success: bool
    message: str
    import_batch_id: int | None = None
