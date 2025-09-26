from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, auth  # <-- IMPORT AUTH

app = FastAPI(
    title="Ishaan: AI Based Supportive Companion",
    description="Backend API to power Ishaan, an emotionally-aware AI companion.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"]) 
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"]) 

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Supportive Companion API!"}