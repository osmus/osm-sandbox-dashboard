from pydantic import BaseModel, Field, validator
from typing import Optional
import datetime
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


class BoxResponse(BoxBase):
    id: int
    subdomain: str
    state: str
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime] = None
    age: Optional[float] = None

    class Config:
        orm_mode = True
        from_attributes = True
