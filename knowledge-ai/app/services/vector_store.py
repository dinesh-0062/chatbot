
import os

import chromadb
import uuid


class VectorStore:

    def __init__(self):

        persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name="knowledge_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, chunks, embeddings, document_id=None, source_id=None, source_type=None, source_title=None):

        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be equal"
            )

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = []

        for index, chunk in enumerate(chunks):
            metadata = {
                "source_type": source_type or "pdf",
                "chunk_index": int(chunk.get("chunk_index", index)),
                "content_hash": chunk.get("content_hash", ""),
            }
            if document_id:
                metadata.update({
                    "document_id": document_id,
                    "source_id": document_id,
                    "source_title": source_title or "",
                    "page": int(chunk["page"]),
                })
            if source_id:
                metadata.update({
                    "source_id": source_id,
                    "source_title": source_title or "",
                    "page_url": chunk.get("page_url", ""),
                    "original_url": chunk.get("original_url", ""),
                    "page": int(chunk.get("page", 0)),
                })
            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=[chunk["text"] for chunk in chunks],
            metadatas=metadatas
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

            metadata_document_id = metadata.get("document_id") or metadata.get("source_id")
            retrieved_chunks.append({
                "text": document,
                "document_id": metadata_document_id,
                "source_id": metadata_document_id,
                "source_type": metadata.get("source_type", "pdf"),
                "source_title": metadata.get("source_title", ""),
                "page": metadata.get("page", 0),
                "page_url": metadata.get("page_url", ""),
                "original_url": metadata.get("original_url", ""),
                "distance": float(distance),
                "chunk_index": metadata.get("chunk_index", 0),
            })

        return retrieved_chunks



    def delete_document(self, document_id: str):
        result = self.collection.get(include=["metadatas"])
        ids = [
            chunk_id
            for chunk_id, metadata in zip(result["ids"], result["metadatas"])
            if metadata.get("document_id") == document_id
            or metadata.get("source_id") == document_id
        ]

        if not ids:
            return 0

        self.collection.delete(ids=ids)

        return len(ids)

