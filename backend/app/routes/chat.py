from fastapi import APIRouter, Depends, HTTPException
from app.schemas import ChatMessage, ChatHistoryMessage, UserInDB, StatusResponse
from app.services.ai_service import get_ai_reply, get_or_create_conversation
from app.services.auth_service import get_current_user
from app.db import conversation_collection
from typing import List

router = APIRouter()

@router.post("/chat", response_model=ChatMessage)
async def handle_chat(
    request: ChatMessage,
    current_user: UserInDB = Depends(get_current_user)
):
    if not request.content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
    
    reply = await get_ai_reply(user=current_user, message=request.content)
    return ChatMessage(content=reply)

@router.get("/history", response_model=List[ChatHistoryMessage])
async def get_chat_history(current_user: UserInDB = Depends(get_current_user)):
    history_from_db = await get_or_create_conversation(current_user.id)
    
    # Filter out the system prompt and the initial "Got it" message
    filtered_history = [
        msg for msg in history_from_db if not msg['parts'][0].startswith("You are Rohan")
    ][1:]
    
    # Transform the data to match the ChatHistoryMessage model (parts -> content)
    response_history = [
        ChatHistoryMessage(role=msg["role"], content=msg["parts"][0])
        for msg in filtered_history
    ]
    
    return response_history

@router.delete("/clear_history", response_model=StatusResponse)
async def clear_chat_history(current_user: UserInDB = Depends(get_current_user)):
    """
    Deletes the entire conversation history for the logged-in user.
    """
    await conversation_collection.delete_one({"user_id": current_user.id})
    return {"message": "Chat history cleared successfully"}