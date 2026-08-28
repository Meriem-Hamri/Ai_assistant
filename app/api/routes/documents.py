from fastapi import APIRouter, Depends, File, UploadFile

from app.api.schemas.document import DocumentResponse
from app.api.dependencies import (
    get_embedding_service,
    get_vector_store,
)
from app.documents.indexer import DocumentIndexer
from app.documents.service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_document_service(
    embedding_service=Depends(
        get_embedding_service
    ),
    vector_store=Depends(
        get_vector_store
    ),
) -> DocumentService:

    indexer = DocumentIndexer(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    return DocumentService(
        indexer=indexer
    )


@router.post(
    "/",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    return await service.upload_document(
        file
    )