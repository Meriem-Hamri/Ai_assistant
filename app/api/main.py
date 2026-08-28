from fastapi import FastAPI

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