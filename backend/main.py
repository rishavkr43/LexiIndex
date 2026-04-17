from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import upload, query, documents, gdoc
from services.poller import start_poller, stop_poller


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_poller()
    yield
    stop_poller()


app = FastAPI(
    title="LexIndex",
    description="AI Knowledge Indexing System — Google Docs Live RAG",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(gdoc.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LexIndex", "version": "2.0.0"}
