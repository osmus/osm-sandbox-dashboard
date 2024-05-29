import os
from fastapi import APIRouter, Request, Depends

from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests_oauthlib import OAuth2Session
from utils.sandbox_database import check_database_instance
from utils.osm_credentials import get_osm_credentials

router = APIRouter()

client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes = (
    get_osm_credentials()
)


oauth = OAuth2Session(
    client_id=client_id, redirect_uri=redirect_uri, scope=osm_instance_scopes
)

@router.get("/oauth_authorization", tags=["Oauth"])
async def get_user_info(code: str):
    try:
        token = oauth.fetch_token(
            f"{osm_instance_url}/oauth2/token", code=code, client_secret=client_secret
        )
        oauth.token = token
        user_details_response = oauth.get(
            f"{osm_instance_url}/api/0.6/user/details.json"
        )
        user_details = user_details_response.json()
        return JSONResponse(content=user_details)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)

# @router.get("/instances/{name}", tags=["Api"])
# async def get_instance_status(name: str):
#     status = check_database_instance(name)
#     return {"name": name, "status": status}
