from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str
