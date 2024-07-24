from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from models.boxes import Boxes, StateEnum
from schemas.boxes import BoxResponse
from utils.kubectl import normalize_status


def is_box_running(db: Session, box_name: str) -> bool:
    """Query the database to check if the box is in the "Running" state"""
    box_record = db.query(Boxes).filter(Boxes.name == box_name).order_by(Boxes.id.desc()).first()
    if box_record and box_record.state == StateEnum.running:
        return True
    return False


def update_box_state_and_age(
    db: Session, box_name: str, releases: list, pod_info: dict
) -> Optional[BoxResponse]:

    db_box = db.query(Boxes).filter(Boxes.name == box_name).order_by(Boxes.id.desc()).first()

    if not db_box:
        return None

    if db_box.state == StateEnum.running:
        box_response = BoxResponse.from_orm(db_box)
        return box_response

    release = next((r for r in releases if r["name"] == box_name), None)
    if release:
        pods = pod_info.get(release["name"], [])
        release_status = [pod.get("state") for pod in pods]
        normalized_status = normalize_status(release_status)
        release["state"] = normalized_status

        if normalized_status == "Running":
            db_box.state = StateEnum.running
        elif normalized_status == "Pending":
            db_box.state = StateEnum.pending
        else:
            db_box.state = StateEnum.failure

        db.commit()
        db.refresh(db_box)

    # Calculate age based on current datetime and start datetime
    current_datetime = datetime.utcnow()
    age_timedelta = current_datetime - db_box.start_date
    age_in_hours = round(age_timedelta.total_seconds() / 3600, 2)

    db_box.age = age_in_hours
    db.commit()
    db.refresh(db_box)

    box_response = BoxResponse.from_orm(db_box)
    box_response.age = age_in_hours

    return box_response
