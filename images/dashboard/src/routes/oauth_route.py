import os
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import Session
from utils.sandbox_database import save_user_sandbox_db
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import update_user_session
from database import get_db

router = APIRouter()

(
    client_id,
    client_secret,
    redirect_uri,
    osm_instance_url,
    osm_instance_scopes,
) = get_osm_credentials()
domain = os.getenv("SANDBOX_DOMAIN")

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
            session_obj = update_user_session(db, unique_id, display_name)
            save_user_sandbox_db(session_obj.get("stack"), session_obj.get("user"))
            # Construct the subdomain URL
            stack = session_obj.get("stack")
            user = session_obj.get("user")
            sub_domain_url = f"https://{stack}.{domain}/login?user={user}"  # noqa: E231
            return RedirectResponse(url=sub_domain_url)
        else:
            raise HTTPException(status_code=404, detail="Check if instance exist")

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)
