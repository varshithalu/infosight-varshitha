from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from pydantic_core import core_schema
from bson import ObjectId
from typing import Any, Optional

# --- PyObjectId CLASS  ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> ObjectId:
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.no_info_plain_validator_function(validate),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    preferences: Optional[dict] = {}
    
    # Use model_config for Pydantic v2
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class UserPublic(UserBase):
    id: PyObjectId = Field(alias="_id")

    # Use model_config for Pydantic v2
    model_config = ConfigDict(
        populate_by_name=True, 
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Chat Schemas ---
class ChatMessage(BaseModel):
    content: str

class ChatHistoryMessage(BaseModel):
    role: str
    content: str

class StatusResponse(BaseModel):
    message: str