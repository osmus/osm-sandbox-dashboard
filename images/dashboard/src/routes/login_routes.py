import logging
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, RedirectResponse
from requests_oauthlib import OAuth2Session
from models.sessions import Sessions
from datetime import datetime

# Import database utils
from database import get_db

# Import utils
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import save_update_box_session, update_user_session
from utils.sandbox_database import save_user_sandbox_db
from utils.box_helpers import is_box_running

from schemas.sessions import SessionResponse
import utils.logging_config

# Get OSM credentials
client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes = (
    get_osm_credentials()
)

router = APIRouter()

domain = os.getenv("SANDBOX_DOMAIN")

oauth = OAuth2Session(client_id=client_id, redirect_uri=redirect_uri, scope=osm_instance_scopes)


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


@router.get("/login_sandbox", tags=["Testing pages"])
def test_page(request: Request, db: Session = Depends(get_db)):
    """Page for login test"""
    logging.info("Accessed /login_sandbox endpoint")
    return templates.TemplateResponse("login_sandbox.html", {"request": request})


@router.get("/initialize_session", tags=["OSM Session Sandbox"], response_model=SessionResponse)
def initialize_session(request: Request, box: str = Query(...), db: Session = Depends(get_db)):
    """Generate and save a new cookie_id"""
    logging.info("Accessed /initialize_session endpoint")
    if not is_box_running(db, box):
        raise HTTPException(
            status_code=400, detail=f'The specified box "{box}" is not available yet!'
        )

    session_id = str(uuid.uuid4())
    new_session = Sessions(id=session_id, box=box, created_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    response = JSONResponse(
        content={
            "id": new_session.id,
            "box": new_session.box,
            "created_at": new_session.created_at.isoformat(),
        }
    )
    # Set cookie_id with session_id
    response.set_cookie(key="cookie_id", value=session_id)
    logging.info("Generated new cookie_id and saved to database")
    return response


@router.get("/osm_authorization", tags=["OSM Session Sandbox"])
def osm_authorization(
    request: Request, session_id: str = Query(...), db: Session = Depends(get_db)
):
    """Enable OSM authorization"""
    logging.info(f"Accessed /osm_authorization with session_id: {session_id}")

    # Verify if session id exists
    db_session = db.query(Sessions).filter(Sessions.id == session_id).first()
    if db_session is None:
        logging.error("session_id not found")
        raise HTTPException(status_code=404, detail="session_id not found")

    # Redirect to OSM auth
    auth_url = f"{osm_instance_url}/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={osm_instance_scopes}"
    logging.info(f"Redirecting to auth URL: {auth_url}")
    return RedirectResponse(url=auth_url, status_code=303)


@router.get("/redirect_sandbox", tags=["OSM Session Sandbox"])
async def redirect_sandbox(request: Request, code: str, db: Session = Depends(get_db)):
    """Redirect and login in sandbox"""
    logging.info(f"Accessed /redirect_sandbox endpoint with code: {code}")

    try:
        # Get user data
        token = oauth.fetch_token(
            f"{osm_instance_url}/oauth2/token", code=code, client_secret=client_secret
        )
        oauth.token = token
        user_details_response = oauth.get(f"{osm_instance_url}/api/0.6/user/details.json")
        user_details = user_details_response.json()
        display_name = user_details.get("user").get("display_name")
        logging.info(f"Fetched user details for: {display_name}")

        # Here is where it gets the session id
        session_id = request.cookies.get("cookie_id")
        if session_id:
            session_obj = update_user_session(db, session_id, display_name)

            save_user_sandbox_db(session_obj.box, session_obj.user)
            logging.info(f"Updated session for session_id: {session_id}")

            # Construct the subdomain URL
            box = session_obj.box
            user = session_obj.user
            sub_domain_url = f"https://{box}.{domain}/login?user={user}"
            logging.info(f"Redirecting to subdomain URL: {sub_domain_url}")
            return RedirectResponse(url=sub_domain_url)
        else:
            logging.error("Cookie ID not found")
            raise HTTPException(status_code=404, detail="Check if instance exists")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
