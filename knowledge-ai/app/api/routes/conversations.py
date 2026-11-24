import uuid
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


@router.post("/")
def create_conversation(db: Session = Depends(get_db)):
    conversation = Conversation(
        conversation_id=str(uuid.uuid4()),
        title="New Chat"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "success": True,
        "conversation": {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "created_at": conversation.created_at
        }
    }


@router.get("/")
def get_conversations(db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return {
        "success": True,
        "total": len(conversations),
        "conversations": [
            {
                "conversation_id": item.conversation_id,
                "title": item.title,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "message_count": len(item.messages)
            }
            for item in conversations
        ]
    }


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "success": True,
        "conversation": {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": [
                {
                    "message_id": message.message_id,
                    "role": message.role,
                    "content": message.content,
                    "sources": message.sources,
                    "created_at": message.created_at
                }
                for message in conversation.messages
            ]
        }
    }


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.title = update.title.strip()
    db.commit()
    db.refresh(conversation)
    return {
        "success": True,
        "conversation": {
            "conversation_id": conversation.conversation_id,
            "title": conversation.title,
        }
    }


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return {
        "success": True,
        "message": "Conversation deleted successfully",
        "conversation_id": conversation_id
    }