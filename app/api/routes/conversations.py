from fastapi import APIRouter


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.get("/")
def list_conversations():
    return {
        "message": "Liste des conversations"
    }