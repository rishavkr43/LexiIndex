from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.routers import upload, query, documents

app = FastAPI(
    title="LexIndex",
    description="AI Knowledge Indexing System for legal document Q&A",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LexIndex"}