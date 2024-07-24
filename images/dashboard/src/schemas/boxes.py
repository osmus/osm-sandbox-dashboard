from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class BoxBase(BaseModel):
    name: str = Field(
        ...,
        title="Box Name",
        description="The unique identifier for the box. Must contain only lowercase letters or hyphens. This name will be used as a subdomain for the box.",
        example="osm-us",
    )
    resource_label: str = Field(
        ...,
        title="Resource Label",
        description="A label that specifies the type of machine where the box will run. The value should be filled with one of the values from the /resources endpoint.",
        example="t3-medium-ondemand",
    )
    owner: str = Field(
        ...,
        title="Owner",
        description="The name or identifier of the person or entity responsible for the box.",
        example="Leya",
    )

    @validator("name")
    def validate_name(cls, value):
        if not re.match("^[a-z-]+$", value):
            raise ValueError("Name must contain only lowercase letters and hyphens")
        return value

    class Config:
        orm_mode = True
        from_attributes = True


class BoxResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    resource_label: str
    owner: str
    state: str
    start_date: datetime
    end_date: Optional[datetime]
    age: Optional[float]

    @staticmethod
    def calculate_age(start_date: datetime) -> float:
        current_date = datetime.utcnow()
        age_in_hours = (current_date - start_date).total_seconds() / 3600
        return round(age_in_hours, 2)

    @staticmethod
    def from_orm(box: "Boxes") -> "BoxResponse":
        box_response = BoxResponse(
            id=box.id,
            name=box.name,
            subdomain=box.subdomain,
            resource_label=box.resource_label,
            owner=box.owner,
            state=box.state,
            start_date=box.start_date,
            end_date=box.end_date,
            age=BoxResponse.calculate_age(box.start_date) if box.start_date else None,
        )
        return box_response

    class Config:
        orm_mode = True
