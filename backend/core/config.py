from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1"
    FRONTEND_URLS: str = "http://localhost:5173"

    EMBEDDING_MODEL: str = "multi-qa-MiniLM-L6-cos-v1"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    SUMMARY_MODEL: str = "llama-3.1-8b-instant"

    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_PAGES: int = 6
    TOP_K_CHUNKS: int = 10

    PINECONE_INDEX_NAME: str = "lexindex"
    PINECONE_NAMESPACE_CHUNKS: str = "chunks"
    PINECONE_NAMESPACE_PAGES: str = "page-index"

    # Google Docs integration
    GOOGLE_CREDENTIALS_PATH: str = "./credentials.json"
    POLL_INTERVAL_SECONDS: int = 60

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_URLS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
