import motor.motor_asyncio
from app.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
db = client.chatbot_db 

# Get collections
user_collection = db.get_collection("users")
conversation_collection = db.get_collection("conversations")