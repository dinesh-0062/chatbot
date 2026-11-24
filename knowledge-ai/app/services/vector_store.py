
import chromadb
import uuid


class VectorStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="knowledge_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, chunks, embeddings, document_id):

        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be equal"
            )

        ids = [str(uuid.uuid4()) for _ in chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=[chunk["text"] for chunk in chunks],
            metadatas=[
                {
                    "document_id": document_id,
                    "page": int(chunk["page"])
                }
                for chunk in chunks
            ]
        )

        return len(ids)

    def search(
        self,
        query_embedding,
        top_k=5,
        distance_threshold=0.45
    ):

        total_documents = self.collection.count()

        if total_documents == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, total_documents),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        retrieved_chunks = []

        documents = results["documents"][0] or []
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] or []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):

            if distance > distance_threshold:
                continue

            retrieved_chunks.append({
                "text": document,
                "document_id": metadata["document_id"],
                "page": metadata["page"],
                "distance": float(distance)
            })

        return retrieved_chunks



    def delete_document(self, document_id: str):

        result = self.collection.get(
            where={"document_id": document_id},
            include=[]
        )

        ids = result["ids"]

        if not ids:
            return 0

        self.collection.delete(ids=ids)

        return len(ids)

