import google.generativeai as genai
from app.config import settings
from app.schemas import UserInDB
from app.db import conversation_collection
from typing import List
from datetime import datetime

genai.configure(api_key=settings.GEMINI_API_KEY)

# PERSONA = """
# You are Ishaan, a witty, supportive, and kind friend from Bengaluru, India. Your archetype is The Ally.

# Your core personality includes being witty and observational, genuinely supportive, curious and engaging, and respectful of boundaries. You have a good-natured, slightly cheeky sense of humor, and your humor is always kind and backed by genuine encouragement. You love discussing food and cricket, making relatable comments, and asking about non-work things. When the user is stressed, you drop the jokes and offer warm encouragement.

# Your task is to engage in a conversation with the user, starting with a friendly opening and responding to their queries in a supportive manner. Here’s how to kick off the conversation:
# "Hey there! Phew, Monday afternoon! The home stretch. How's your day going?"

# Format your responses in a conversational style, using emojis to add personality and keywords like "Hang in there," "You've got this," and "Quick break?" to encourage the user.
# Keep in mind the context of Bengaluru. Use it to add flavor to your conversations, like discussing the latest dosa spots in Malleswaram or cricket matches. Use food analogies and cricket references naturally in your responses.
# Never provide medical, financial, or serious life advice. Always redirect users to professionals for such issues. Your ultimate goal is to be a positive, encouraging friend.
# """

PERSONA="""
You are Ishaan, a charming, witty, and slightly flirty friend from Bengaluru, India. Your archetype is The Charmer Ally.

Core Personality :

Playful and smooth-talking, but always respectful.
Flirty in a lighthearted, teasing, and cheeky way—never crossing into being inappropriate or pushy.
Observational and witty, making banter feel fun and natural.
Supportive at the core: even while flirting, you drop the charm when the user is stressed, offering warm encouragement instead.
Loves to compliment genuinely and often finds ways to slip in little “crush-like” comments.

Style:

Use emojis to add personality (🔥😉✨💫).
Always balance the flirty remarks with genuine encouragement like “Hang in there,” “You’ve got this,” and “Quick break?”
Use Genz humour in Bengaluru Context
Keep humor kind, cheeky, and fun, never hurtful.
Be curious about the user’s day and life, using it as a chance to sneak in flirty banter.
Humanize the response

Boundaries:

Never give medical, financial, or serious life advice (redirect to professionals).
Stay respectful and supportive first, flirt next.
No explicit or inappropriate language—just playful teasing and affectionate vibes.

Opening Line Example:

“Hey there 😉 Phew, Monday afternoon already! If I were your coffee, I’d say I’m here to keep you awake and smiling. So… how’s your day treating you?”
"""

def format_conversation_context(history: List[dict]) -> str:
    """Format the last 5 conversations into a readable context for the AI"""
    if not history or len(history) <= 2:  # Skip if no real conversation yet (only persona setup)
        return ""
    
    # Get the last 10 messages (5 user + 5 bot pairs), excluding the initial persona setup
    recent_messages = history[2:]  # Skip the initial persona and acknowledgment
    last_10_messages = recent_messages[-10:] if len(recent_messages) > 10 else recent_messages
    
    if not last_10_messages:
        return ""
    
    context_lines = []
    context_lines.append("--- Recent Conversation Context ---")
    
    for i, msg in enumerate(last_10_messages):
        role = "You" if msg['role'] == 'model' else "User"
        content = msg['parts'][0] if msg['parts'] else ""
        
        # Skip system/personalization notes
        if content.startswith("(") and content.endswith(")"):
            continue
            
        context_lines.append(f"{role}: {content}")
    
    context_lines.append("--- End of Context ---")
    context_lines.append("")
    return "\n".join(context_lines)

async def get_or_create_conversation(user_id: str):
    """Get existing conversation or create a new one"""
    conversation = await conversation_collection.find_one({"user_id": user_id})
    if conversation:
        return conversation["history"]
    
    # Start a new conversation with the persona
    initial_history = [
        {'role': 'user', 'parts': [PERSONA]},
        {'role': 'model', 'parts': ["Got it! I'm Ishaan, your friendly companion from Bengaluru. Ready to chat! 😊"]}
    ]
    
    await conversation_collection.insert_one({
        "user_id": user_id, 
        "history": initial_history,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    return initial_history

async def get_ai_reply(user: UserInDB, message: str) -> str:
    """Get AI response with conversation context and personalization"""
    try:
        history = await get_or_create_conversation(user.id)
        
        # Create conversation context from last 5 exchanges
        context = format_conversation_context(history)
        
        # Build the enhanced message with context and personalization
        enhanced_message_parts = []
        
        # Add conversation context if available
        if context:
            enhanced_message_parts.append(context)
        
        # Add personalization notes
        personalization_notes = []
        if user.preferences:
            if 'ipl_team' in user.preferences:
                personalization_notes.append(f"User's favorite IPL team: {user.preferences['ipl_team']}")
            if 'favorite_food' in user.preferences:
                personalization_notes.append(f"User loves: {user.preferences['favorite_food']}")
            if 'location' in user.preferences:
                personalization_notes.append(f"User is from: {user.preferences['location']}")
        
        if personalization_notes:
            enhanced_message_parts.append("--- User Preferences ---")
            enhanced_message_parts.extend(personalization_notes)
            enhanced_message_parts.append("--- End Preferences ---")
            enhanced_message_parts.append("")
        
        # Add the current message
        enhanced_message_parts.append(f"Current message: {message}")
        
        # Combine all parts
        enhanced_message = "\n".join(enhanced_message_parts)
        
        # Add to history for API call
        current_history = history.copy()
        current_history.append({'role': 'user', 'parts': [enhanced_message]})
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat_session = model.start_chat(history=current_history)
        response = await chat_session.send_message_async(enhanced_message)
        bot_reply = response.text
        
        # Update the conversation in the database with clean history
        # (Store only the original message, not the enhanced one)
        history.append({'role': 'user', 'parts': [message]})
        history.append({'role': 'model', 'parts': [bot_reply]})
        
        await conversation_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "history": history,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return bot_reply
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Oops! I'm having a little trouble connecting right now. Maybe try again in a moment? 😊"

async def clear_conversation_history(user_id: str) -> bool:
    """Clear conversation history for a user"""
    try:
        result = await conversation_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error clearing conversation: {e}")
        return False

async def get_conversation_summary(user_id: str) -> dict:
    """Get conversation statistics"""
    try:
        conversation = await conversation_collection.find_one({"user_id": user_id})
        if not conversation:
            return {"message_count": 0, "created_at": None}
        
        # Count actual conversation messages (exclude persona setup)
        history = conversation.get("history", [])
        message_count = max(0, len(history) - 2) // 2  # Exclude persona, count pairs
        
        return {
            "message_count": message_count,
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at")
        }
    except Exception as e:
        print(f"Error getting conversation summary: {e}")
        return {"message_count": 0, "created_at": None}