
import logging
import uuid

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.rag import RAGService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["RAG Chat"]
)


@lru_cache(maxsize=1)
def get_rag_service():
    return RAGService()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    conversation_id: str | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


@router.post("/ask")
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # CREATE OR GET CONVERSATION

        if request.conversation_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.conversation_id == request.conversation_id
                )
                .first()
            )

            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )

        else:
            conversation = Conversation(
                conversation_id=str(uuid.uuid4()),
                title=request.question[:60]
            )

            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # FETCH PREVIOUS MESSAGES

        previous_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.conversation_id
            )
            .order_by(Message.created_at.desc())
            .limit(8)
            .all()
        )

        conversation_history = [
            {
                "role": message.role,
                "content": message.content
            }
            for message in reversed(previous_messages)
        ]

        # SAVE USER MESSAGE

        user_message = Message(
            message_id=str(uuid.uuid4()),
            conversation_id=conversation.conversation_id,
            role="user",
            content=request.question
        )

        db.add(user_message)

        conversation.updated_at = func.now()
        db.commit()
        db.refresh(user_message)

        # PROCESS RAG

        rag_service = get_rag_service()

        result = rag_service.ask(
            question=request.question,
            top_k=request.top_k,
            conversation_history=conversation_history
        )

        answer = result["answer"]
        sources = result.get("sources", [])

        # SAVE ASSISTANT MESSAGE

        assistant_message = Message(
            message_id=str(uuid.uuid4()),
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=answer,
            sources=sources
        )

        db.add(assistant_message)

        conversation.updated_at = func.now()

        db.commit()
        db.refresh(assistant_message)

        return {
            "success": True,
            "conversation_id": conversation.conversation_id,
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": result.get("retrieved_chunks", 0),
            "messages": {
                "user_message_id": user_message.message_id,
                "assistant_message_id": assistant_message.message_id
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        logger.exception("RAG chat request failed")

        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {type(error).__name__}"
        )
