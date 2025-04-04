import google.oauth2.credentials
import google_auth_oauthlib.flow
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import GOOGLE_CLIENT_SECRET
from app.services.google.auth import credentials_to_dict

router = APIRouter()

# Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


@router.get("/authenticated")
async def index(request: Request):
    """Home page with authentication link"""
    if request.session.get("google_credentials"):
        return request.session["google_credentials"]

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
    return {"url": authorization_url}


@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    """Handle OAuth callback"""
    state = request.query_params.get("state")
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
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found")

    # Store the credentials in the session
    if "session" in request.scope:
        request.session["google_credentials"] = credentials_to_dict(credentials)

    return RedirectResponse(url="http://localhost:3000/auth/success", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """Revoke credentials and clear session"""
    if "google_credentials" in request.session:
        credentials = google.oauth2.credentials.Credentials(
            **request.session["google_credentials"]
        )

        revoke_response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": credentials.token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if revoke_response.status_code == 200:
            request.session.pop("google_credentials", None)
            return {"message": "User has been logged out and credentials revoked"}
        else:
            return {"error": f"Failed to revoke token: {revoke_response.text}"}

    return {"message": "No credentials found in session"}
