
from functools import lru_cache
import os
import re

from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.groq_service import GroqService


@lru_cache(maxsize=1)
def get_embedding_service():
    return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


@lru_cache(maxsize=1)
def get_groq_service():
    return GroqService()


class RAGService:

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.groq_service = get_groq_service()

    def ask(
        self,
        question: str,
        top_k: int = 5,
        conversation_history: list | None = None
    ):

        # GREETING HANDLING

        normalized_question = question.strip().lower()

        greetings = {
            "hi",
            "hello",
            "hey",
            "hi there",
            "hello there",
            "good morning",
            "good afternoon",
            "good evening",
            "good night"
        }

        if normalized_question in greetings:

            return {
                "answer": (
                    "Hello! Welcome to Knowledge AI. "
                    "You can upload your PDF documents and ask me "
                    "questions about them. How can I help you today?"
                ),
                "sources": [],
                "retrieved_chunks": 0
            }

        # Retrieval uses only the current question. Conversation history is
        # supplied later for intent resolution, never as source evidence.
        retrieval_query = re.sub(r"\s+", " ", question).strip()

        # GENERATE QUERY EMBEDDING

        query_embedding = (
            self.embedding_service.generate_query_embedding(
                retrieval_query
            )
        )

        # VECTOR SEARCH

        top_k = int(top_k)
        distance_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))
        retrieved_chunks = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            distance_threshold=distance_threshold
        )

        # NO RELEVANT DOCUMENTS

        if not retrieved_chunks:
            answer = (
                "I couldn't find sufficient information about this question "
                "in your indexed sources."
            )
            lowered = normalized_question
            if re.search(r"[а-я]", lowered, re.I):
                pass
            if re.search(r"[\\u0900-\\u097f]", question):
                answer = (
                    "Mujhe aapke indexed sources mein is sawaal ka kafi "
                    "relevant information nahi mila."
                )
                if re.search(r"[\\u0900-\\u097f]", question):
                    answer = (
                        "मुझे आपके indexed sources में इस प्रश्न का पर्याप्त "
                        "प्रासंगिक उत्तर नहीं मिला।"
                    )

            return {
                "answer": answer,
                "sources": [],
                "retrieved_chunks": 0
            }

        # BUILD CONTEXT

        context_parts = []
        sources = []
        max_context_chars = int(os.getenv("MAX_RAG_CONTEXT_CHARS", "12000"))

        unique = []
        seen = set()
        for chunk in retrieved_chunks:
            signature = re.sub(r"\W+", " ", chunk["text"].lower()).strip()[:300]
            if signature in seen:
                continue
            seen.add(signature)
            unique.append(chunk)

        for index, chunk in enumerate(unique, start=1):

            reference = f"[{index}]"

            if sum(len(part) for part in context_parts) >= max_context_chars:
                break

            if chunk["source_type"] == "web":
                context_parts.append(
                    f"Reference: {reference}\n"
                    f"Source: {chunk.get('source_title') or 'Web documentation'}\n"
                    f"Page URL: {chunk.get('page_url') or chunk.get('original_url') or ''}\n"
                    f"Content:\n{chunk['text']}"
                )
            else:
                context_parts.append(
                    f"Reference: {reference}\n"
                    f"Document ID: {chunk['document_id']}\n"
                    f"Document: {chunk.get('source_title') or 'PDF document'}\n"
                    f"Page: {chunk['page']}\n"
                    f"Content:\n{chunk['text']}"
                )

            source = {
                "reference": reference,
                "document_id": chunk["document_id"],
                "source_id": chunk["source_id"],
                "source_type": chunk["source_type"],
                "source_title": chunk.get("source_title") or "",
                "page": chunk["page"],
                "page_url": chunk.get("page_url") or "",
                "original_url": chunk.get("original_url") or "",
                "distance": chunk["distance"],
            }
            sources.append(source)

        context = "\n".join(context_parts)

        # GENERATE GROQ ANSWER

        answer = self.groq_service.generate_answer(
            question=question,
            context=context,
            conversation_history=conversation_history
        )

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(retrieved_chunks)
        }
