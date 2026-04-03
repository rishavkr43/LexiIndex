from sentence_transformers import SentenceTransformer
from core.config import settings
import numpy as np


class Embedder:
    _instance: "Embedder | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._instance

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return vectors.tolist()

    def embed_one(self, text: str) -> list[float]:
        vector = self._model.encode([text], normalize_embeddings=True)
        return vector[0].tolist()


embedder = Embedder()