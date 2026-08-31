from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from app.api.dependencies import (
    get_document_repository,
    get_embedding_service,
    get_metadata_extractor,
    get_vector_store,
)
from app.api.schemas.document import DocumentResponse
from app.documents.indexer import DocumentIndexer
from app.documents.repository import DocumentRepository
from app.documents.service import (
    DocumentDeletionConflictError,
    DocumentService,
)


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
    metadata_extractor=Depends(
        get_metadata_extractor
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
        metadata_extractor=metadata_extractor,
    )


@router.post(
    "/",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    category: str | None = Form(None),
    year: int | None = Form(None),
    person: str | None = Form(None),
    department: str | None = Form(None),
    document_type: str | None = Form(None),
    tags: list[str] | None = Form(None),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    return await service.upload_document(
        file,
        title=title,
        category=category,
        year=year,
        person=person,
        department=department,
        document_type=document_type,
        tags=tags,
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


@router.get(
    "/{document_id}/file",
    response_class=FileResponse,
)
def get_document_file(
    document_id: str,
    download: bool = False,
    service: DocumentService = Depends(
        get_document_service
    ),
):
    """Affiche le fichier, ou le télécharge avec ?download=true."""

    try:
        document_file = service.get_document_file(document_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Fichier du document indisponible.",
        )

    if document_file is None:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable.",
        )

    file_path, metadata = document_file
    media_types = {
        "pdf": "application/pdf",
        "docx": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    }

    return FileResponse(
        path=file_path,
        media_type=media_types.get(
            metadata.get("type"),
            "application/octet-stream",
        ),
        filename=metadata["filename"],
        content_disposition_type=(
            "attachment" if download else "inline"
        ),
    )

@router.delete(
    "/{document_id}",
)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(
        get_document_service
    ),
):
    try:
        deleted = service.delete_document(
            document_id
        )
    except DocumentDeletionConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable.",
        )

    return {
        "message": "Document supprimé avec succès."
    }

