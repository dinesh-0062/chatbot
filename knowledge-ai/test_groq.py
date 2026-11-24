
from app.services.groq_service import GroqService

groq_service = GroqService()

answer = groq_service.generate_answer(
    question="What is RAG?",
    context="""
    RAG stands for Retrieval-Augmented Generation.
    It combines information retrieval with language generation.
    """
)

print("\nGroq response:\n")
print(answer)
