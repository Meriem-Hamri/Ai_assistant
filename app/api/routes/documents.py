from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from app.api.dependencies import (
    get_document_repository,
    get_embedding_service,
    get_vector_store,
)
from app.api.schemas.document import DocumentResponse
from app.documents.indexer import DocumentIndexer
from app.documents.repository import DocumentRepository
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
    repository: DocumentRepository = Depends(
        get_document_repository
    ),
) -> DocumentService:

    indexer = DocumentIndexer(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    return DocumentService(
        indexer=indexer,
        repository=repository,
        vector_store=vector_store,
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


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def get_documents(
    service: DocumentService = Depends(
        get_document_service
    ),
):
    return service.get_documents()

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: str,
    service: DocumentService = Depends(
        get_document_service
    ),
):
    document = service.get_document(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable.",
        )

    return document

@router.delete(
    "/{document_id}",
)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(
        get_document_service
    ),
):
    deleted = service.delete_document(
        document_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable.",
        )

    return {
        "message": "Document supprimé avec succès."
    }

