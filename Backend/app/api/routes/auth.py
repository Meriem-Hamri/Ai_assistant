from fastapi import FastAPI

from app.api.routes import documents
from app.api.routes import conversations
from app.api.routes import chat


app = FastAPI(
    title="Assistant AI",
    description="Assistant intelligent pour documents internes",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Assistant AI API",
        "status": "running",
    }


app.include_router(documents.router)
app.include_router(conversations.router)
app.include_router(chat.router)