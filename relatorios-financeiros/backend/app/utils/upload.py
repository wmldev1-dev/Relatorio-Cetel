"""Adaptadores para arquivos recebidos pela API."""

from __future__ import annotations

from io import BytesIO


class NamedBytesIO(BytesIO):
    """BytesIO com atributo name para compatibilidade com servicos existentes."""

    def __init__(self, content: bytes, name: str) -> None:
        super().__init__(content)
        self.name = name
