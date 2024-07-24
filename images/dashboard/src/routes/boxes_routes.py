import os
import re
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, validator, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc
import logging
import asyncio

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
from utils.box_helpers import update_box_state_and_age, check_release_status
import utils.logging_config

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
        .order_by(desc(Boxes.id))
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

    # Start the job to check the release status for the next 5 minutes
    asyncio.create_task(check_release_status(namespace, db_box.id, db))

    return BoxResponse.from_orm(db_box)


@router.get(
    "/boxes",
    tags=["Boxes"],
    response_model=List[BoxResponse],
    description="List all currently active boxes.",
)
async def get_boxes(db: Session = Depends(get_db)):
    try:
        logging.info("Fetching all active boxes from the database.")

        # Fetch only boxes with states Pending, Running, and Failure
        boxes = (
            db.query(Boxes)
            .filter(Boxes.state.in_([StateEnum.pending, StateEnum.running, StateEnum.failure]))
            .order_by(desc(Boxes.id))
            .all()
        )

        box_responses = [BoxResponse.from_orm(box) for box in boxes]

        logging.info("Fetched all active boxes successfully.")
        return box_responses
    except Exception as e:
        logging.error(f"Error fetching boxes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/boxes/{box_name}",
    tags=["Boxes"],
    response_model=BoxResponse,
    description="Get an active box by name.",
)
async def get_box(box_name: str, db: Session = Depends(get_db)):
    try:
        logging.info(f"Fetching box with name: {box_name}.")

        # Fetch the box with the given name and state in Pending, Running, or Failure
        box = (
            db.query(Boxes)
            .filter(
                Boxes.name == box_name,
                Boxes.state.in_([StateEnum.pending, StateEnum.running, StateEnum.failure]),
            )
            .first()
        )

        if not box:
            logging.warning(f"Box with name {box_name} not found.")
            raise HTTPException(status_code=404, detail="Box not found")

        box_response = BoxResponse.from_orm(box)

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

        db_box = (
            db.query(Boxes)
            .filter(Boxes.name == box_name, Boxes.state != StateEnum.terminated)
            .order_by(desc(Boxes.id))
            .first()
        )

        if not db_box:
            logging.warning(f"Box with name {box_name} not found or already terminated.")
            raise HTTPException(status_code=404, detail="Box not found or already terminated")

        # Set end_date and calculate age
        end_datetime = datetime.utcnow()
        db_box.end_date = end_datetime
        db_box.state = StateEnum.terminated
        age_in_hours = BoxResponse.calculate_age(db_box.start_date)
        db_box.age = age_in_hours
        result = await delete_release(box_name, namespace)
        db.commit()
        db.refresh(db_box)

        box_response = BoxResponse.from_orm(db_box)

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
