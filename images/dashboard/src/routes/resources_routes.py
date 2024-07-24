import os
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Annotated
from sqlalchemy.orm import Session
from database import get_db
from models.resources import Resources
from utils.kubectl import list_nodes
import utils.logging_config

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter()


@router.get("/resources", tags=["Resources"])
async def get_resources(db: db_dependency):
    try:
        nodes = await list_nodes()
        resources = db.query(Resources).all()

        resource_list = []
        for resource in resources:
            node_list = nodes.get(resource.label, [])
            resource_dict = {
                "id": resource.id,
                "label": resource.label,
                "inst_cpu": resource.inst_cpu,
                "inst_ram": resource.inst_ram,
                "max_inst_allowed": resource.max_inst_allowed,
                "num_inst_active": len(node_list),
                "nodes": node_list,
            }
            resource_list.append(resource_dict)

        return resource_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
