import os
import re
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from database import get_db
from utils.helm import (
    list_releases,
    replace_placeholders_and_save,
    create_upgrade_box,
    delete_release,
)
from utils.kubectl import list_pods, normalize_status
from models.boxes import Boxes, StateEnum
from schemas.boxes import BoxBase, BoxResponse
from utils.box_helpers import update_box_state_and_age


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
router = APIRouter()
namespace = "default"
sandbox_domain = os.getenv("SANDBOX_DOMAIN")


@router.post(
    "/boxes",
    tags=["Boxes"],
    response_model=BoxResponse,
    description="Create a box in the database and release a sack in the Kubernetes cluster.",
)
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


@router.get(
    "/boxes",
    tags=["Boxes"],
    response_model=List[BoxResponse],
    description="List all currently active boxes.",
)
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

        sorted_box_responses = sorted(box_responses, key=lambda x: x.id)

        logging.info("Fetched all boxes successfully.")
        return sorted_box_responses
    except Exception as e:
        logging.error(f"Error fetching boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/boxes/{box_name}",
    tags=["Boxes"],
    response_model=BoxResponse,
    description="List an active box by name.",
)
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


@router.delete(
    "/boxes/{box_name}",
    tags=["Boxes"],
    description="Delete an active box and update its end date and age in the database.",
)
async def delete_box(box_name: str, db: Session = Depends(get_db)):
    try:
        logging.info(f"Attempting to delete box with name: {box_name}.")

        db_box = db.query(Boxes).filter(Boxes.name == box_name).first()
        if not db_box:
            logging.warning(f"Box with name {box_name} not found.")
            raise HTTPException(status_code=404, detail="Box not found")

        # Set end_date and calculate age
        end_datetime = datetime.utcnow()
        db_box.end_date = end_datetime
        db_box.state = StateEnum.terminated

        age_timedelta = end_datetime - db_box.start_date
        age_in_hours = round(age_timedelta.total_seconds() / 3600, 2)

        db_box.age = age_in_hours
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


@router.get(
    "/boxes_history",
    tags=["Boxes"],
    response_model=List[BoxResponse],
    description="Fetch a paginated history of boxes from the database.",
)
async def get_boxes_history(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    try:
        logging.info("Fetching boxes history from the database with pagination.")
        offset = (page - 1) * page_size
        boxes = db.query(Boxes).order_by(Boxes.id.desc()).offset(offset).limit(page_size).all()
        box_responses = [
            BoxResponse(
                id=box.id,
                name=box.name,
                state=box.state,
                age=box.age,
                resource_label=box.resource_label,
                owner=box.owner,
                subdomain=box.subdomain,
                start_date=box.start_date.isoformat() if box.start_date else None,
                end_date=box.end_date.isoformat() if box.end_date else None,
            )
            for box in boxes
        ]

        logging.info("Fetched boxes history successfully.")
        return box_responses
    except Exception as e:
        logging.error(f"Error fetching boxes history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
