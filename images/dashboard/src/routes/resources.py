import os
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated
from sqlalchemy.orm import Session
from database import get_db
from models.resources import Resources
from pydantic import BaseModel, Field
from utils.kubectl_resources import list_nodes

class NodeInfo(BaseModel):
    name: str
    instance_type: str = Field(..., alias='instance-type')
    region: str
    zone: str

class ResourceBase(BaseModel):
    id: int
    label: str
    cpu: int
    ram: int
    nodes: List[NodeInfo] = []  # Add this field to include nodes information

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter()

@router.get("/resources", tags=["Resources"], response_model=List[ResourceBase])
async def get_resources(db: db_dependency):
    try:
        nodes = await list_nodes()
        resources = db.query(Resources).all()

        # Assuming you want to merge node information into the resources based on label
        resource_list = []
        for resource in resources:
            resource_dict = {
                "id": resource.id,
                "label": resource.label,
                "cpu": resource.cpu,
                "ram": resource.ram,
                "nodes": nodes.get(resource.label, [])  # Fetch nodes based on the label
            }
            resource_list.append(resource_dict)

        return resource_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
