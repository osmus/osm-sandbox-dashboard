from pydantic import BaseModel
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CREATOR = "creator"
    USER = "user"


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
