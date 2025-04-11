import json
import logging

import google.oauth2.credentials
import google_auth_oauthlib.flow
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleAuthRequest

from app.core.config import GOOGLE_CLIENT_SECRET, GOOGLE_SCOPES
from app.services.google.auth import credentials_to_dict

router = APIRouter()
logger = logging.getLogger(__name__)


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
        GOOGLE_CLIENT_SECRET, scopes=GOOGLE_SCOPES
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
        GOOGLE_CLIENT_SECRET, scopes=GOOGLE_SCOPES, state=state
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


@router.get("/oauth/refresh")
async def refresh_token(request: Request):
    """
    Refresh the user's Google access token if needed.

    Returns:
        JSON with refresh status
    """
    if "session" not in request.scope or "google_credentials" not in request.session:
        raise HTTPException(
            status_code=401,
            detail={"message": "Not authenticated with Google", "refreshed": False},
        )

    try:
        google_credentials = request.session["google_credentials"]

        # Check if credentials dictionary has minimum required fields
        required_fields = ["token", "refresh_token", "client_id", "client_secret"]
        for field in required_fields:
            if field not in google_credentials:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": f"Missing required credential field: {field}",
                        "refreshed": False,
                    },
                )

        # Create credentials object
        credentials = google.oauth2.credentials.Credentials(
            token=google_credentials["token"],
            refresh_token=google_credentials["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=google_credentials["client_id"],
            client_secret=google_credentials["client_secret"],
        )

        # Check if expired and refresh if needed
        if credentials.refresh_token:
            request_object = GoogleAuthRequest()
            credentials.refresh(request_object)

            # Update the session with the refreshed credentials
            request.session["google_credentials"] = credentials_to_dict(credentials)

            return {
                "message": "Token refreshed successfully",
                "refreshed": True,
                "platform": "youtube",
            }

        # No refresh token, can't refresh
        if "refresh_token" not in google_credentials:
            await logout(request)
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "No refresh token available, please login again. ",
                    "refreshed": False,
                    "platform": "youtube",
                },
            )

        return {
            "message": "Token is still valid",
            "refreshed": False,
            "platform": "youtube",
        }

    except Exception as e:
        logger.error("Error refreshing Google token: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error refreshing token: {str(e)}",
                "refreshed": False,
                "platform": "youtube",
            },
        ) from e


@router.get("/logout")
async def logout(request: Request):
    """Revoke credentials and clear session"""
    if "google_credentials" not in request.session:
        return {
            "message": "No active session found",
            "platform": "youtube",
        }

    revocation_successful = False
    error_message = None

    try:
        credentials = google.oauth2.credentials.Credentials(
            **request.session["google_credentials"]
        )

        # Attempt to revoke the token
        revoke_response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": credentials.token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        revocation_successful = revoke_response.status_code == 200

        if not revocation_successful:
            # Try to get error details if available
            try:
                error_details = revoke_response.json()
                error_message = (
                    f"Revocation failed: {error_details.get('error', 'Unknown error')}"
                )
            except ValueError:
                error_message = (
                    f"Revocation failed with status code: {revoke_response.status_code}"
                )

    except Exception as e:
        logger.error("Error during token revocation: %s", str(e))
        error_message = f"Error during token revocation: {str(e)}"

    finally:
        # Always clear the session, regardless of revocation result
        request.session.pop("google_credentials", None)

    if revocation_successful:
        return {
            "message": "User has been logged out and credentials revoked",
            "platform": "youtube",
        }

    return {
        "message": "Session cleared, but token revocation failed",
        "error": error_message,
        "platform": "youtube",
    }
