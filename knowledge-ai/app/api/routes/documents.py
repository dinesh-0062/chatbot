import os
import uuid
from functools import lru_cache

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.services.pdf_loader import PDFLoader
from app.services.chunker import TextChunker
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "data/uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    document_id = str(uuid.uuid4())
    stored_filename = f"{document_id}.pdf"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    vector_store = get_vector_store()
    vectors_added = False
    db_committed = False

    try:
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF size must not exceed 20 MB"
            )

        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        with open(file_path, "wb") as pdf_file:
            pdf_file.write(content)

        loader = PDFLoader()
        chunker = TextChunker()
        embedding_service = EmbeddingService()

        pages = loader.load(file_path)

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF"
            )

        chunks = chunker.split(pages)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not generate text chunks from this PDF"
            )

        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings(texts)

        total_chunks = vector_store.add_documents(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id
        )
        vectors_added = True

        document = Document(
            document_id=document_id,
            original_filename=os.path.basename(file.filename)[:255],
            stored_filename=stored_filename,
            total_pages=len(pages),
            total_chunks=total_chunks,
            status="completed"
        )

        db.add(document)
        db.commit()
        db_committed = True
        db.refresh(document)

        return {
            "success": True,
            "message": "Document uploaded and indexed successfully",
            "document": {
                "document_id": document.document_id,
                "original_filename": document.original_filename,
                "total_pages": document.total_pages,
                "total_chunks": document.total_chunks,
                "status": document.status,
                "created_at": document.created_at
            }
        }

    except HTTPException:
        db.rollback()

        if db_committed:
            existing = db.query(Document).filter(
                Document.document_id == document_id
            ).first()
            if existing:
                db.delete(existing)
                db.commit()

        if vectors_added:
            vector_store.delete_document(document_id)

        if os.path.exists(file_path):
            os.remove(file_path)

        raise

    except Exception as exc:
        db.rollback()

        if db_committed:
            existing = db.query(Document).filter(
                Document.document_id == document_id
            ).first()
            if existing:
                db.delete(existing)
                db.commit()

        if vectors_added:
            vector_store.delete_document(document_id)

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {str(exc)}"
        )


@router.get("/")
def get_documents(db: Session = Depends(get_db)):
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "total_documents": len(documents),
        "documents": [
            {
                "document_id": doc.document_id,
                "original_filename": doc.original_filename,
                "total_pages": doc.total_pages,
                "total_chunks": doc.total_chunks,
                "status": doc.status,
                "created_at": doc.created_at,
                "file_exists": os.path.exists(
                    os.path.join(UPLOAD_DIR, doc.stored_filename)
                )
            }
            for doc in documents
        ]
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    try:
        uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    document = db.query(Document).filter(
        Document.document_id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    vector_store = get_vector_store()
    file_path = os.path.join(UPLOAD_DIR, document.stored_filename)

    try:
        # Mark the document first, so an interrupted deletion can be retried.
        document.status = "deleting"
        db.commit()

        # Remove embeddings from ChromaDB.
        deleted_chunks = vector_store.delete_document(document_id)

        # Remove the original PDF.
        file_deleted = False
        if os.path.exists(file_path):
            os.remove(file_path)
            file_deleted = True

        # Remove the PostgreSQL record last.
        db.delete(document)
        db.commit()

        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id,
            "deleted_chunks": deleted_chunks,
            "file_deleted": file_deleted
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Document deletion failed: {str(exc)}"
        )