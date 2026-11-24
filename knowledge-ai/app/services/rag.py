
from functools import lru_cache

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

        # CONVERSATION-AWARE RETRIEVAL

        previous_questions = []

        if conversation_history:

            for message in conversation_history:

                if message.get("role") == "user":

                    content = message.get("content", "").strip()

                    if content:
                        previous_questions.append(content)

        recent_questions = previous_questions[-2:]

        retrieval_query = "\n".join(
            recent_questions + [question]
        )

        # GENERATE QUERY EMBEDDING

        query_embedding = (
            self.embedding_service.generate_query_embedding(
                retrieval_query
            )
        )

        # VECTOR SEARCH

        retrieved_chunks = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            distance_threshold=0.45
        )

        # NO RELEVANT DOCUMENTS

        if not retrieved_chunks:

            return {
                "answer": (
                    "I could not find relevant information "
                    "in the uploaded documents. "
                    "Please try another question."
                ),
                "sources": [],
                "retrieved_chunks": 0
            }

        # BUILD CONTEXT

        context_parts = []
        sources = []

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1
        ):

            reference = f"[{index}]"

            context_parts.append(
                f"""
Reference: {reference}
Document ID: {chunk['document_id']}
Page: {chunk['page']}

Content:
{chunk['text']}
"""
            )

            sources.append({
                "reference": reference,
                "document_id": chunk["document_id"],
                "page": chunk["page"],
                "distance": chunk["distance"]
            })

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
