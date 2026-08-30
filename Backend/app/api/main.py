from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents
from app.api.routes import conversations
from app.api.routes import chat


app = FastAPI(
    title="Assistant AI",
    description="Assistant intelligent pour documents internes",
    version="1.0.0",
)

# Le frontend Next.js est servi localement sur le port 3000 pendant le
# développement. Les deux origines sont autorisées pour fonctionner avec
# localhost comme avec 127.0.0.1.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
