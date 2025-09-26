from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import Token, UserCreate, UserPublic, LoginRequest
from app.services import auth_service, user_service
from app.config import settings

router = APIRouter()

@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    db_user = await user_service.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = await user_service.create_user(user)
    return created_user

@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Authenticates the user with email and password and returns a JWT access token.
    """
    user = await user_service.get_user_by_email(request.email)
    if not user or not user_service.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # The 'sub' (subject) of the token is the user's email, which uniquely identifies them
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}