from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    GROQ_API_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    SUMMARY_MODEL: str = "llama-3.1-8b-instant"

    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_PAGES: int = 3
    TOP_K_CHUNKS: int = 5

    CHROMA_PERSIST_DIR: str = "./chroma_store"
    CHUNKS_COLLECTION: str = "chunks"
    PAGE_INDEX_COLLECTION: str = "page_index"

    class Config:
        env_file = "backend/.env"

settings = Settings()
CHROMA_PATH = Path(settings.CHROMA_PERSIST_DIR)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)