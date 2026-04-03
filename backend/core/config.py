from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1"
    FRONTEND_URLS: str = "http://localhost:5173"

    EMBEDDING_MODEL: str = "paraphrase-MiniLM-L3-v2"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    SUMMARY_MODEL: str = "llama-3.1-8b-instant"

    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_PAGES: int = 3
    TOP_K_CHUNKS: int = 5

    PINECONE_INDEX_NAME: str = "lexindex"
    PINECONE_NAMESPACE_CHUNKS: str = "chunks"
    PINECONE_NAMESPACE_PAGES: str = "page-index"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_URLS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
