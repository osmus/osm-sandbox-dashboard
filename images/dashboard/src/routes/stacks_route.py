from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated
from models import stacks_models as models
from sqlalchemy.orm import Session
import datetime
from database import get_db

router = APIRouter()


class StackBase(BaseModel):
    name: str
    status: str
    start_date: datetime.date
    end_date: datetime.date


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/stacks", response_model=StackBase, tags=["Stacks"])
async def create_stack(stack: StackBase, db: db_dependency):
    db_stack = models.Stacks(
        name=stack.name,
        status=stack.status,
        start_date=stack.start_date,
        end_date=stack.end_date,
    )
    db.add(db_stack)
    db.commit()
    db.refresh(db_stack)
    return db_stack


@router.get("/stacks", tags=["Stacks"])
async def get_stacks(db: db_dependency):
    result = db.query(models.Stacks).all()
    if not result:
        raise HTTPException(status_code=404, detail="Stacks not found")
    return result
