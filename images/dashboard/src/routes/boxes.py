import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Annotated, List
from sqlalchemy.orm import Session
import datetime
from database import get_db
from utils.helm_deploy import (
    list_releases,
    replace_placeholders_and_save,
    create_upgrade,
)
from utils.kubectl_deploy import list_pods, normalize_status
from models import boxes as models

router = APIRouter()


class BoxBase(BaseModel):
    name: str
    status: str
    start_date: datetime.date
    end_date: datetime.date


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/boxes", response_model=BoxBase, tags=["Boxes"])
async def create_box(box: BoxBase, db: db_dependency):

    # create values files
    os.environ["BOX_NAME"] = box.name
    values_file = f"values/values_{box.name}.yaml"
    replace_placeholders_and_save("values/osm-seed.template.yaml", values_file)
    # create a new box

    try:
        output = await create_upgrade(box.name, values_file)
        print(output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db_box = models.Boxes(
        name=box.name,
        status=box.status,
        start_date=box.start_date,
        end_date=box.end_date,
    )

    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box


@router.get("/boxes", tags=["Boxes"])
async def get_boxes(db: Session = Depends(get_db)):
    namespace = "default"
    try:
        releases = await list_releases(namespace)
        pod_info = list_pods(namespace)

        for release in releases:
            release_name = release["name"]
            pods = pod_info.get(release_name, [])

            release_status = [pod.get("status") for pod in pods]
            release["status"] = normalize_status(release_status)
            release["pods"] = pods

        return releases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
