from fastapi import FastAPI

from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router


app = FastAPI(title="Local Knowledge Chat Backend")

app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
