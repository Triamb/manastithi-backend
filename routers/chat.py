import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from services.ai_service import ai_service
from services.supabase_service import supabase_service
from services.auth import verify_supabase_token, require_auth
from services.rate_limit import chat_rate_limit

logger = logging.getLogger("manastithi.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


# Explicit OPTIONS handler for CORS preflight
@router.options("/message")
async def options_message():
    return Response(status_code=200)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    messages: List[Dict[str, str]]


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(chat_rate_limit)])
async def send_message(
    request: ChatRequest,
    user: Optional[dict] = Depends(verify_supabase_token),
):
    """
    Send a message to Mana and get a response.
    Allows anonymous access (for landing page chat) but authenticated
    users get conversation history persistence.
    """
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # SECURITY: Only use authenticated user_id - never trust client-supplied user_id
    effective_user_id = user["id"] if user else None

    # Get conversation history for context
    conversation_history = []
    if effective_user_id:
        conversation_history = await supabase_service.get_conversation_history(
            effective_user_id,
            limit=10,
        )

    # Generate AI response
    ai_response = await ai_service.chat(
        message=message,
        conversation_history=conversation_history,
    )

    # Save messages to database (if user is authenticated)
    if effective_user_id:
        await supabase_service.save_message(
            user_id=effective_user_id,
            message=message,
            sender="user",
        )
        await supabase_service.save_message(
            user_id=effective_user_id,
            message=ai_response,
            sender="ai",
        )

    return ChatResponse(
        response=ai_response,
        session_id=request.session_id,
    )


@router.get("/history/{user_id}", response_model=ConversationHistoryResponse)
async def get_history(
    user_id: str,
    limit: int = Query(default=50, le=100, ge=1),
    current_user: dict = Depends(require_auth),
):
    """Get conversation history for a user. Requires authentication."""
    # Users can only access their own history
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's history")

    history = await supabase_service.get_conversation_history(user_id, limit)
    return ConversationHistoryResponse(messages=history)


@router.delete("/history/{user_id}")
async def clear_history(
    user_id: str,
    current_user: dict = Depends(require_auth),
):
    """Clear conversation history for a user. Requires authentication."""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Cannot clear another user's history")

    if not supabase_service.client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        supabase_service.client.table("chat_logs") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()
        return {"message": "History cleared"}
    except Exception as e:
        logger.error(f"Failed to clear history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear history")
