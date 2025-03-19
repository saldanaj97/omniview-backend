import os

import google.oauth2.credentials
import google_auth_oauthlib.flow
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.core.config import GOOGLE_CLIENT_SECRET
from app.services.google.auth import credentials_to_dict

router = APIRouter()

# Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# For development only - disable in production
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# OAuth2 scheme for authorization
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/authorize", tokenUrl="/oauth2callback"
)


@router.get("/authenticate")
async def index(request: Request):
    """Home page with authentication link"""
    if request.session.get("credentials"):
        return request.session["credentials"]

    return {
        "message": "YouTube Live Broadcasts API",
        "authenticate": f"{request.url_for('authorize')}",
    }


@router.get("/authorize")
async def authorize(request: Request):
    """Initiate OAuth flow"""
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        GOOGLE_CLIENT_SECRET, scopes=SCOPES
    )

    flow.redirect_uri = str(request.url_for("oauth2callback"))

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )

    request.session["state"] = state
    return RedirectResponse(url=authorization_url)


@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    """Handle OAuth callback"""
    state = request.session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="State not found in session")

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        GOOGLE_CLIENT_SECRET, scopes=SCOPES, state=state
    )
    flow.redirect_uri = str(request.url_for("oauth2callback"))

    # Get the authorization response URL
    authorization_response = str(request.url)
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in session
    credentials = flow.credentials
    request.session["credentials"] = credentials_to_dict(credentials)

    return RedirectResponse(url="/api/google/auth")


@router.get("/revoke")
async def revoke(request: Request):
    """Revoke OAuth token"""
    if "credentials" not in request.session:
        return {"message": "No credentials to revoke"}

    credentials = google.oauth2.credentials.Credentials(
        **request.session["credentials"]
    )

    revoke_response = requests.post(
        "https://oauth2.googleapis.com/revoke",
        params={"token": credentials.token},
        headers={"content-type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if revoke_response.status_code == 200:
        request.session.pop("credentials", None)
        return {"message": "Credentials successfully revoked"}
    else:
        return {"message": f"An error occurred: {revoke_response.text}"}


@router.get("/clear")
async def clear_credentials(request: Request):
    """Clear credentials from session"""
    if "credentials" in request.session:
        request.session.pop("credentials", None)
    return {"message": "Credentials have been cleared"}
