"""Rotas de diagnostico de importacao."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.import_processor_service import ImportProcessorService
from app.services.diagnostico_campos_service import DiagnosticoCamposService

router = APIRouter(prefix="/api/diagnostico", tags=["diagnostico"])


@router.get("/importacoes/{import_batch_id}", response_model=dict[str, Any])
def diagnosticar_importacao(import_batch_id: int) -> dict[str, object]:
    """Retorna diagnostico de uma importacao."""
    try:
        return ImportProcessorService().get_import_diagnostics(import_batch_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/campos", response_model=dict[str, Any])
def diagnosticar_campos(competencia: str) -> dict[str, object]:
    """Retorna diagnostico de preenchimento dos campos financeiros."""
    try:
        return DiagnosticoCamposService().diagnosticar(competencia)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
