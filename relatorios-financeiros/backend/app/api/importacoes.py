"""Rotas de importacoes."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.common import MessageResponse
from app.schemas.importacao import ImportacaoCreateResponse, ImportacaoResponse
from app.services.import_processor_service import ImportProcessorService
from app.services.import_service import ImportService
from app.utils.upload import NamedBytesIO

router = APIRouter(prefix="/api/importacoes", tags=["importacoes"])


@router.get("", response_model=list[ImportacaoResponse])
def listar_importacoes() -> list[dict[str, str]]:
    """Lista importacoes registradas."""
    return ImportService().list_imports()


@router.post("", response_model=ImportacaoCreateResponse, status_code=status.HTTP_201_CREATED)
async def criar_importacao(
    competencia: str = Form(...),
    arquivo: UploadFile = File(...),
) -> ImportacaoCreateResponse:
    """Registra um arquivo SQL para processamento posterior."""
    upload = NamedBytesIO(await arquivo.read(), arquivo.filename or "")
    success, message, import_batch_id = ImportService().register_import(
        competencia,
        upload,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return ImportacaoCreateResponse(
        success=success,
        message=message,
        import_batch_id=import_batch_id,
    )


@router.get("/{import_batch_id}", response_model=ImportacaoResponse)
def buscar_importacao(import_batch_id: int) -> dict[str, str]:
    """Busca uma importacao pelo identificador."""
    try:
        return ImportService().get_import(import_batch_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{import_batch_id}/processar", response_model=MessageResponse)
def processar_importacao(import_batch_id: int) -> MessageResponse:
    """Processa uma importacao registrada."""
    success, message = ImportProcessorService().process_import(import_batch_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return MessageResponse(success=success, message=message)


@router.post("/{import_batch_id}/reprocessar", response_model=MessageResponse)
def reprocessar_importacao(import_batch_id: int) -> MessageResponse:
    """Reprocessa uma importacao apagando e recriando seus lancamentos."""
    success, message = ImportProcessorService().reprocess_import(import_batch_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return MessageResponse(success=success, message=message)


@router.delete("/{import_batch_id}", response_model=MessageResponse)
def remover_importacao(import_batch_id: int) -> MessageResponse:
    """Remove uma importacao e seus lancamentos financeiros."""
    try:
        success, message = ImportService().delete_import(import_batch_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return MessageResponse(success=success, message=message)
