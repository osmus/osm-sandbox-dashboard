from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated
import logging

from database import get_db
from models.users import User, UserRole
from schemas.users import UserCreate, UserOut, Token
from security import (
    get_password_hash,
    get_current_user,
    authenticate_user,
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from utils.auth import create_access_token, TokenData
import utils.logging_config

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    tags=["Dashboard authentication"],
    response_model=UserOut,
    description="Register a user, by default with user role",
)
def register(user: UserCreate, db: db_dependency):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", tags=["Dashboard authentication"], response_model=Token, description="Login")
def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    logging.info(f"Login attempt for user: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logging.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": [user.role.value]}, expires_delta=access_token_expires
    )
    logging.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
