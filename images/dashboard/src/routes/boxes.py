import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator, ValidationError
from typing import Annotated, List
from sqlalchemy.orm import Session
import datetime
import re

from database import get_db
from utils.helm_deploy import (
    list_releases,
    replace_placeholders_and_save,
    create_upgrade,
    delete_release,
)
from utils.kubectl_deploy import list_pods, normalize_status
from models import boxes as models

router = APIRouter()
namespace = "default"


class BoxBase(BaseModel):
    name: str
    resource_label: str
    owner: str

    @validator("name")
    def validate_name(cls, value):
        if not re.match("^[a-z-]+$", value):
            raise ValueError("Name must contain only lowercase letters and hyphens")
        return value


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/boxes", tags=["Boxes"])
async def create_box(box: BoxBase, db: Session = Depends(get_db)):
    # Create values file
    values_file = replace_placeholders_and_save(box.name, box.resource_label)

    # Create a new box
    try:
        output, deploy_date, status = await create_upgrade(box.name, namespace, values_file)
        print(output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if status == "failure":
        raise HTTPException(status_code=500, detail="Deployment failed: " + output)

    db_box = models.Boxes(
        name=box.name,
        resource_label=box.resource_label,
        owner=box.owner,
        status="deployed",
        start_date=deploy_date,
    )

    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box


@router.get("/boxes", tags=["Boxes"])
async def get_boxes(db: Session = Depends(get_db)):
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


@router.delete("/boxes/{box_name}", tags=["Boxes"])
async def delete_box(box_name: str, db: Session = Depends(get_db)):
    try:
        # Call the function to delete the release
        result = await delete_release(box_name, namespace)
        return {"detail": f"Release {box_name} deleted successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
