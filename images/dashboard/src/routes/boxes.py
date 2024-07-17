import os
import re
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from database import get_db
from utils.helm_deploy import (
    list_releases,
    replace_placeholders_and_save,
    create_upgrade_box,
    delete_release,
)
from utils.kubectl_deploy import list_pods, normalize_status
from models.boxes import Boxes, StateEnum
from schemas.boxes import BoxBase, BoxResponse
from utils.box_helpers import update_box_state_and_age

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
router = APIRouter()
namespace = "default"
sandbox_domain = os.getenv("SANDBOX_DOMAIN")


@router.post("/boxes", tags=["Boxes"], response_model=BoxResponse)
async def create_box(box: BoxBase, db: Session = Depends(get_db)):
    logging.info("Attempting to create a new box.")

    # Check if there is an existing box with the same name and state "Running" or "Pending"
    existing_box = (
        db.query(Boxes)
        .filter(Boxes.name == box.name, Boxes.state.in_([StateEnum.running, StateEnum.pending]))
        .first()
    )

    if existing_box:
        logging.warning(f"Resource with the name {box.name} is already running or pending.")
        raise HTTPException(
            status_code=400, detail="Resource with the same name is already running or pending"
        )

    # Create values file
    values_file = replace_placeholders_and_save(box.name, box.resource_label)

    # Create a new box
    try:
        output, deploy_date, state = await create_upgrade_box(box.name, namespace, values_file)
        logging.info(f"Upgrade box output: {output}")
    except Exception as e:
        logging.error(f"Error creating box: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    if state == "Failure":
        logging.error(f"Deployment failed: {output}")
        raise HTTPException(status_code=500, detail="Deployment failed: " + output)

    db_box = Boxes(
        name=box.name,
        subdomain=f"{box.name}.{sandbox_domain}",
        resource_label=box.resource_label,
        owner=box.owner,
        state=StateEnum[state],
        start_date=datetime.strptime(deploy_date, "%Y-%m-%d %H:%M:%S"),
    )

    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    logging.info(f"Box {box.name} created successfully.")
    return BoxResponse.from_orm(db_box)


@router.get("/boxes", tags=["Boxes"], response_model=List[BoxResponse])
async def get_boxes(db: Session = Depends(get_db)):
    try:
        logging.info("Fetching all boxes.")
        releases = await list_releases(namespace)
        pod_info = list_pods(namespace)

        box_responses = []
        for release in releases:
            box_response = update_box_state_and_age(db, release["name"], releases, pod_info)
            if box_response:
                box_responses.append(box_response)

        logging.info("Fetched all boxes successfully.")
        return box_responses
    except Exception as e:
        logging.error(f"Error fetching boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/boxes/{box_name}", tags=["Boxes"], response_model=BoxResponse)
async def get_box(box_name: str, db: Session = Depends(get_db)):
    try:
        logging.info(f"Fetching box with name: {box_name}.")
        releases = await list_releases(namespace)
        pod_info = list_pods(namespace)

        box_response = update_box_state_and_age(db, box_name, releases, pod_info)
        if not box_response:
            logging.warning(f"Box with name {box_name} not found.")
            raise HTTPException(status_code=404, detail="Box not found")

        logging.info(f"Fetched box {box_name} successfully.")
        return box_response
    except Exception as e:
        logging.error(f"Error fetching box {box_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/boxes/{box_name}", tags=["Boxes"])
async def delete_box(box_name: str, db: Session = Depends(get_db)):
    try:
        logging.info(f"Attempting to delete box with name: {box_name}.")

        # Fetch the box from the database
        db_box = db.query(Boxes).filter(Boxes.name == box_name).first()
        if not db_box:
            logging.warning(f"Box with name {box_name} not found.")
            raise HTTPException(status_code=404, detail="Box not found")

        # Set end_date and calculate age
        end_datetime = datetime.utcnow()
        db_box.end_date = end_datetime
        db_box.state = StateEnum.terminated

        age_timedelta = end_datetime - db_box.start_date
        age_in_hours = age_timedelta.total_seconds() // 3600  # Age in hours

        # Call the function to delete the release
        result = await delete_release(box_name, namespace)

        db.commit()
        db.refresh(db_box)

        box_response = BoxResponse.from_orm(db_box)
        box_response.age = age_in_hours

        logging.info(f"Box {box_name} deleted successfully.")
        return {
            "detail": f"Release {box_name} deleted successfully",
            "result": result,
            "box": box_response,
        }
    except Exception as e:
        logging.error(f"Error deleting box {box_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
