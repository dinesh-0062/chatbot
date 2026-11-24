import os
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.web_source import WebSource
from app.services.chunker import TextChunker
from app.services.embedding import EmbeddingService
from app.services.url_validator import UnsafeURLException
from app.services.vector_store import VectorStore
from app.services.web_loader import WebLoadError, WebLoader


router = APIRouter(prefix="/sources", tags=["Knowledge Sources"])


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


@lru_cache(maxsize=1)
def get_embedding_service():
    return EmbeddingService()


class WebSourceRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


def _index_web_source(db: Session, source: WebSource) -> WebSource:
    vector_store = get_vector_store()
    loader = WebLoader()
    try:
        loaded = loader.load(source.original_url)
        source.canonical_url = loaded["canonical_url"]
        source.title = loaded["title"]
        source.content_hash = loaded["content_hash"]
        source.status = "processing"
        source.error_message = None
        db.commit()

        chunks = TextChunker().split_text(loaded["text"])
        for index, chunk in enumerate(chunks):
            chunk["chunk_index"] = index
            chunk["content_hash"] = loaded["content_hash"]
            chunk["page_url"] = loaded["canonical_url"]
            chunk["original_url"] = loaded["original_url"]

        embeddings = get_embedding_service().generate_embeddings(
            [chunk["text"] for chunk in chunks]
        )
        vector_store.delete_document(source.source_id)
        total_chunks = vector_store.add_documents(
            chunks=chunks,
            embeddings=embeddings,
            source_id=source.source_id,
            source_type="web",
            source_title=source.title,
        )

        source.total_chunks = total_chunks
        source.status = "completed"
        source.error_message = None
        source.last_indexed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(source)
        return source
    except (UnsafeURLException, WebLoadError, ValueError) as exc:
        source.status = "failed"
        source.error_message = str(exc)
        db.commit()
        db.refresh(source)
        return source
    except Exception as exc:
        source.status = "failed"
        source.error_message = "Website indexing failed."
        db.commit()
        db.refresh(source)
        raise HTTPException(status_code=500, detail="Website indexing failed.") from exc


@router.post("/url")
def add_web_source(request: WebSourceRequest, db: Session = Depends(get_db)):
    source = WebSource(
        source_id=str(uuid.uuid4()),
        original_url=request.url.strip(),
        canonical_url=request.url.strip(),
        title="Web Documentation",
        status="processing",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        source = _index_web_source(db, source)
    except HTTPException:
        raise

    if source.status == "failed":
        return {
            "success": False,
            "source": _serialize_web_source(source),
            "detail": source.error_message,
        }

    return {"success": True, "source": _serialize_web_source(source)}


def _serialize_web_source(source: WebSource) -> dict:
    return {
        "source_id": source.source_id,
        "source_type": "web",
        "title": source.title,
        "original_url": source.original_url,
        "canonical_url": source.canonical_url,
        "total_chunks": source.total_chunks,
        "status": source.status,
        "error_message": source.error_message,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
        "last_indexed_at": source.last_indexed_at,
    }


@router.get("/")
def list_sources(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    web_sources = db.query(WebSource).order_by(WebSource.created_at.desc()).all()

    sources = []
    for document in documents:
        sources.append({
            "source_id": document.document_id,
            "source_type": "pdf",
            "title": document.original_filename,
            "original_url": None,
            "canonical_url": None,
            "total_chunks": document.total_chunks,
            "status": document.status,
            "error_message": document.error_message,
            "file_size": document.file_size,
            "total_pages": document.total_pages,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        })
    sources.extend(_serialize_web_source(source) for source in web_sources)
    sources.sort(key=lambda item: item["created_at"], reverse=True)

    return {"success": True, "total": len(sources), "sources": sources}


@router.get("/{source_id}")
def get_source(source_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.document_id == source_id).first()
    if document:
        return {"success": True, "source": {
            "source_id": document.document_id,
            "source_type": "pdf",
            "title": document.original_filename,
            "total_chunks": document.total_chunks,
            "status": document.status,
            "error_message": document.error_message,
            "file_size": document.file_size,
            "total_pages": document.total_pages,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }}
    source = db.query(WebSource).filter(WebSource.source_id == source_id).first()
    if source:
        return {"success": True, "source": _serialize_web_source(source)}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/{source_id}/refresh")
def refresh_source(source_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.document_id == source_id).first()
    if document:
        file_path = os.path.join("data/uploads", document.stored_filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=422, detail="The original PDF file is unavailable.")
        try:
            from app.services.pdf_loader import PDFLoader
            pages = PDFLoader().load(file_path)
            if not pages:
                raise ValueError("No readable text was found in this PDF.")
            chunks = TextChunker().split(pages)
            embeddings = get_embedding_service().generate_embeddings([chunk["text"] for chunk in chunks])
            get_vector_store().delete_document(document.document_id)
            total_chunks = get_vector_store().add_documents(
                chunks=chunks,
                embeddings=embeddings,
                document_id=document.document_id,
                source_type="pdf",
                source_title=document.original_filename,
            )
            document.total_pages = len(pages)
            document.total_chunks = total_chunks
            document.status = "completed"
            document.error_message = None
            db.commit()
            db.refresh(document)
            return {
                "success": True,
                "source": {
                    "source_id": document.document_id,
                    "source_type": "pdf",
                    "title": document.original_filename,
                    "total_chunks": document.total_chunks,
                    "status": document.status,
                },
            }
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
            db.commit()
            raise HTTPException(status_code=422, detail=document.error_message)

    source = db.query(WebSource).filter(WebSource.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source = _index_web_source(db, source)
    if source.status == "failed":
        raise HTTPException(status_code=422, detail=source.error_message)
    return {"success": True, "source": _serialize_web_source(source)}


@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.document_id == source_id).first()
    web_source = db.query(WebSource).filter(WebSource.source_id == source_id).first()
    if not document and not web_source:
        raise HTTPException(status_code=404, detail="Source not found")

    deleted_chunks = get_vector_store().delete_document(source_id)
    if document:
        file_path = os.path.join("data/uploads", document.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.delete(document)
    if web_source:
        db.delete(web_source)
    db.commit()
    return {"success": True, "message": "Source deleted successfully", "deleted_chunks": deleted_chunks}
