
import os

from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts):

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        return vectors.tolist()

    def generate_query_embedding(self, query: str):

        vector = self.model.encode(
            query,
            normalize_embeddings=True
        )

        return vector.tolist()
