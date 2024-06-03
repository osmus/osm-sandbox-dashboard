import os
from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Import database utils
from database import get_db

# Import utils
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import save_update_stack_session

(
    client_id,
    client_secret,
    redirect_uri,
    osm_instance_url,
    osm_instance_scopes,
) = get_osm_credentials()

router = APIRouter()


# Custom static files to set cache control
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response


static_path = os.path.join(os.path.dirname(__file__), "./../static")
router.mount("/static", CustomStaticFiles(directory=static_path), name="static")

templates_path = os.path.join(os.path.dirname(__file__), "./../templates")
templates = Jinja2Templates(directory=templates_path)

router = APIRouter()


# Home route
@router.get("/", tags=["Home"])
def home(request: Request, stack: str = Query(None), db: Session = Depends(get_db)):
    """Home endpoint for user login."""
    unique_id = request.cookies.get("unique_id")
    # Check stack is not null
    if stack is None:
        raise HTTPException(status_code=404, detail="Stack not found")
    if unique_id and stack:
        save_update_stack_session(db, unique_id, stack)
    req_obj = {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "osm_instance_url": osm_instance_url,
        "osm_instance_scopes": osm_instance_scopes,
        "stack": stack,
        "unique_id": unique_id,
    }
    return templates.TemplateResponse("index.html", req_obj)
