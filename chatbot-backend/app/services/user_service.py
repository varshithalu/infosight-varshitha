from passlib.context import CryptContext
from app.db import user_collection
from app.schemas import UserCreate, UserInDB

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user_by_email(email: str):
    user = await user_collection.find_one({"email": email})
    if user:
        return UserInDB(**user)
    return None

async def create_user(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    # Create the UserInDB model without the password fields
    db_user = UserInDB(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password
    )
    
    # model_dump will now create a dict that MongoDB can handle
    user_dict = db_user.model_dump(by_alias=True)
    
    await user_collection.insert_one(user_dict)
    return db_user