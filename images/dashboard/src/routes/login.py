import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, RedirectResponse
from requests_oauthlib import OAuth2Session
import uuid

# Import database utils
from database import get_db

# Import utils
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import save_update_stack_session, update_user_session
from utils.sandbox_database import save_user_sandbox_db

(
    client_id,
    client_secret,
    redirect_uri,
    osm_instance_url,
    osm_instance_scopes,
) = get_osm_credentials()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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


@router.get("/login_sandbox", tags=["OSM Sandbox"])
def test_page(request: Request, stack: str = Query(None), db: Session = Depends(get_db)):
    """Page for login test"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/osm_authorization", tags=["OSM Sandbox"])
def osm_authorization(request: Request, stack: str = Query(...), db: Session = Depends(get_db)):
    """Enable OSM authorization"""

    cookie_id = request.cookies.get("cookie_id")

    if cookie_id is None:
        # Generate a new cookie_id
        cookie_id = str(uuid.uuid4())
        response = RedirectResponse(url=request.url)
        response.set_cookie(key="cookie_id", value=cookie_id)
        return response

    if cookie_id and stack:
        save_update_stack_session(db, cookie_id, stack)
        auth_url = f"{osm_instance_url}/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={osm_instance_scopes}"
        return RedirectResponse(url=auth_url, status_code=303)
    else:
        raise HTTPException(status_code=404, detail="stack or cookie_id not found")


@router.get("/redirect_sandbox", tags=["OSM Sandbox"])
async def redirect_sandbox(request: Request, code: str, db: Session = Depends(get_db)):
    """Redirect and login in sandbox"""

    try:
        ## Get user data
        token = oauth.fetch_token(
            f"{osm_instance_url}/oauth2/token", code=code, client_secret=client_secret
        )
        oauth.token = token
        user_details_response = oauth.get(f"{osm_instance_url}/api/0.6/user/details.json")
        user_details = user_details_response.json()
        display_name = user_details.get("user").get("display_name")
        # languages = user_details.get("user").get("languages")

        cookie_id = request.cookies.get("cookie_id")
        if cookie_id:
            session_obj = update_user_session(db, cookie_id, display_name)
            save_user_sandbox_db(session_obj.get("stack"), session_obj.get("user"))
            # Construct the subdomain URL
            stack = session_obj.get("stack")
            user = session_obj.get("user")
            sub_domain_url = f"https://{stack}.{domain}/login?user={user}"  # noqa: E231
            return RedirectResponse(url=sub_domain_url)
        else:
            raise HTTPException(status_code=404, detail="Check if instance exist")

    except Exception as e:
        logging.error(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
