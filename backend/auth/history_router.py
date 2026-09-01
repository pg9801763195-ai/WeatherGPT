"""
FastAPI Router for Assistant Conversation History.
Strictly enforces authenticated user ownership on all endpoints to prevent IDOR attacks.
Endpoints:
- GET    /api/assistant/history
- GET    /api/assistant/history/{conversation_id}
- POST   /api/assistant/conversations
- DELETE /api/assistant/history/{conversation_id}
- PATCH  /api/assistant/history/{conversation_id}
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from config import AgentConfig
from db.mongo_database import MongoDatabaseManager
from auth.security import require_auth

config = AgentConfig()
db = MongoDatabaseManager.get_instance(config.mongodb_uri, config.mongodb_db_name)
router = APIRouter(prefix="/api/assistant", tags=["Assistant History"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Initial conversation title")


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="New conversation title")


@router.get("/history")
async def list_user_history(user: dict = Depends(require_auth)):
    """
    Returns all saved conversation sessions belonging strictly to the authenticated user.
    Prevents unauthorized access and IDOR by deriving user ID solely from verified JWT.
    """
    user_id = user["id"]
    conversations = db.get_user_conversations(user_id=user_id, limit=60)
    return {
        "status": "success",
        "count": len(conversations),
        "conversations": conversations
    }


@router.get("/history/{conversation_id}")
async def get_conversation_details(conversation_id: str, user: dict = Depends(require_auth)):
    """
    Retrieves full message timeline for a specific conversation.
    STRICT IDOR PROTECTION: Query filters by both conversation_id AND authenticated user_id.
    """
    user_id = user["id"]
    conv = db.get_conversation_with_messages(conv_id=conversation_id, user_id=user_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return {
        "status": "success",
        "conversation": conv
    }


@router.post("/conversations")
async def create_new_conversation(req: CreateConversationRequest, user: dict = Depends(require_auth)):
    """
    Creates a new conversation thread owned by the authenticated user.
    """
    user_id = user["id"]
    title = req.title or "New Weather Conversation"
    conv = db.create_conversation(user_id=user_id, title=title)
    return {
        "status": "success",
        "conversation": {
            "id": conv["_id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"]
        }
    }


@router.delete("/history/{conversation_id}")
async def delete_conversation_history(conversation_id: str, user: dict = Depends(require_auth)):
    """
    Deletes a conversation and its messages.
    STRICT IDOR PROTECTION: Only deletes if conversation is owned by the authenticated user.
    """
    user_id = user["id"]
    deleted = db.delete_conversation(conv_id=conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return {
        "status": "success",
        "message": "Conversation deleted successfully."
    }


@router.patch("/history/{conversation_id}")
async def update_conversation_title(
    conversation_id: str,
    req: UpdateConversationRequest,
    user: dict = Depends(require_auth)
):
    """
    Renames a conversation thread.
    STRICT IDOR PROTECTION: Only updates if owned by the authenticated user.
    """
    user_id = user["id"]
    updated = db.update_conversation_title(
        conv_id=conversation_id,
        user_id=user_id,
        new_title=req.title
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return {
        "status": "success",
        "message": "Conversation title updated successfully."
    }
