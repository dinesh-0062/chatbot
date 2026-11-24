
import os
from functools import lru_cache

from app.services.vector_store import VectorStore


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


class DocumentService:

    def __init__(self):
        self.vector_store = get_vector_store()
        self.upload_dir = "data/uploads"

    def list_documents(self):

        result = self.vector_store.collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in result["metadatas"]:

            document_id = metadata["document_id"]

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "total_chunks": 0
                }

            documents[document_id]["total_chunks"] += 1

        return list(documents.values())

    def delete_document(self, document_id: str):

        file_path = os.path.join(
            self.upload_dir,
            f"{document_id}.pdf"
        )

        deleted_chunks = self.vector_store.delete_document(
            document_id
        )

        file_deleted = False

        if os.path.exists(file_path):
            os.remove(file_path)
            file_deleted = True

        return {
            "document_id": document_id,
            "deleted_chunks": deleted_chunks,
            "file_deleted": file_deleted
        }
