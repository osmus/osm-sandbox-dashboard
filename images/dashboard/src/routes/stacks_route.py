from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated
from models import stacks_models as models
from sqlalchemy.orm import Session
import datetime
from database import get_db
from utils.helm_deploy import list_releases
from utils.kubectl_deploy import list_pods


router = APIRouter()


class StackBase(BaseModel):
    name: str
    status: str
    start_date: datetime.date
    end_date: datetime.date


db_dependency = Annotated[Session, Depends(get_db)]

# @router.post("/stacks", response_model=StackBase, tags=["Stacks"])
# async def create_stack(stack: StackBase, db: db_dependency):
#     db_stack = models.Stacks(
#         name=stack.name,
#         status=stack.status,
#         start_date=stack.start_date,
#         end_date=stack.end_date,
#     )
#     db.add(db_stack)
#     db.commit()
#     db.refresh(db_stack)
#     return db_stack


@router.get("/boxes", tags=["Boxes"])
async def get_boxes(db: Session = Depends(get_db)):
    namespace = "default"
    try:
        releases = await list_releases(namespace)
        pods = list_pods(namespace)
        for release in releases:
            release_name = release["name"]
            release["pods"] = pods.get(release_name, [])
        return releases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
