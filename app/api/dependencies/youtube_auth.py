import google.oauth2.credentials
from fastapi import HTTPException, Request
from google.auth.transport.requests import Request as GoogleAuthRequest

from app.utils.http_utils import ensure_session_credentials


async def require_google_auth(request: Request):
    """
    Dependency that checks for Google authentication in the session.
    Returns Google credentials if authenticated.
    Raises HTTPException with 401 status code if not authenticated.
    """
    ensure_session_credentials(request, "google_credentials", "Google")
    google_credentials = request.session["google_credentials"]

    # Check if credentials dictionary has minimum required fields
    required_fields = ["token", "refresh_token", "client_id", "client_secret"]
    for field in required_fields:
        if field not in google_credentials or google_credentials[field] is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid credentials",
                    "message": f"Missing required credential field: {field}. Please login again.",
                },
            )

    try:
        credentials = google.oauth2.credentials.Credentials(
            token=google_credentials["token"],
            refresh_token=google_credentials["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=google_credentials["client_id"],
            client_secret=google_credentials["client_secret"],
        )

        # Check if token is expired and refresh if possible
        if credentials.expired and credentials.refresh_token:
            request_object = GoogleAuthRequest()
            credentials.refresh(request_object)

            # Update the session with the refreshed credentials
            request.session["google_credentials"] = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            }
        elif credentials.expired:
            # Token is expired and can't be refreshed
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Token expired",
                    "message": "Your session has expired and cannot be refreshed. Please login again.",
                },
            )

        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication error",
                "message": f"Failed to create credentials object: {str(e)}. Please login again.",
            },
        ) from e
