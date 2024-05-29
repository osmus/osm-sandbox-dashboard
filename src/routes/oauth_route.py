import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import Session
from utils.sandbox_database import check_database_instance
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import update_session
from database import get_db
from utils.sandbox_database import save_user_sandbox_db

router = APIRouter()

client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes = (
    get_osm_credentials()
)

oauth = OAuth2Session(
    client_id=client_id, redirect_uri=redirect_uri, scope=osm_instance_scopes
)

@router.get("/oauth_authorization", tags=["Oauth"])
async def get_user_info(request: Request, code: str, db: Session = Depends(get_db)):
    try:
        token = oauth.fetch_token(
            f"{osm_instance_url}/oauth2/token", code=code, client_secret=client_secret
        )
        oauth.token = token
        user_details_response = oauth.get(
            f"{osm_instance_url}/api/0.6/user/details.json"
        )
        user_details = user_details_response.json()
        display_name = user_details.get("user").get("display_name")

        # Update user in session
        unique_id = request.cookies.get("unique_id")
        if unique_id:
            session_obj = update_session(db, unique_id, display_name)
            save_user_sandbox_db(session_obj.get("stack"), session_obj.get("user"))

        # Add user in the Sandbox DB
        
        
        return {"display_name": display_name}
    
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
