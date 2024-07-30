from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Annotated, List
import logging

from database import get_db
from models.users import User, UserRole
from schemas.users import UserOut
from utils.auth import verify_token, TokenData, verify_role
import utils.logging_config

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db)]


class ChangeUserRoleRequest(BaseModel):
    username: str
    new_role: UserRole


@router.post(
    "/change_role",
    tags=["Users Management"],
    response_model=UserOut,
    description="Change the role of a user. Only accessible by admins.",
    dependencies=[Depends(verify_token)],
)
async def change_user_role(
    request: ChangeUserRoleRequest, db: db_dependency, token: TokenData = Depends(verify_token)
):
    verify_role(token, ["admin"])  # Only admin can change roles

    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        logging.warning(f"User {request.username} not found.")
        raise HTTPException(status_code=404, detail="User not found")

    user.role = request.new_role
    db.commit()
    db.refresh(user)
    logging.info(f"User {request.username} role changed to {request.new_role}.")

    return user


@router.get(
    "/list_users",
    tags=["Users Management"],
    response_model=List[UserOut],
    description="List all users. Only accessible by admins.",
    dependencies=[Depends(verify_token)],
)
async def list_users(db: db_dependency, token: TokenData = Depends(verify_token)):
    verify_role(token, ["admin"])  # Only admin can list users

    users = db.query(User).all()
    if not users:
        logging.warning("No users found.")
        raise HTTPException(status_code=404, detail="No users found")

    logging.info("Fetched all users successfully.")
    return users
