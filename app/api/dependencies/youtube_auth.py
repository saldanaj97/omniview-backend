import google.oauth2.credentials
from fastapi import HTTPException, Request
from google.auth.transport.requests import Request as GoogleAuthRequest


async def require_google_auth(request: Request):
    """
    Dependency that checks for Google authentication in the session.
    Returns Google credentials if authenticated.
    Raises HTTPException with 401 status code if not authenticated.
    """
    if "google_credentials" not in request.session:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "User not authenticated",
                "message": "Please login to access this resource.",
            },
        )

    google_credentials = request.session["google_credentials"]

    # Check if credentials dictionary has minimum required fields
    required_fields = ["token", "refresh_token", "client_id", "client_secret"]
    for field in required_fields:
        if field not in google_credentials:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid credentials",
                    "message": f"Missing required credential field: {field}",
                },
            )

    try:
        credentials = google.oauth2.credentials.Credentials(**google_credentials)

        # Verify credentials are valid
        if not credentials.valid:
            raise ValueError("Credentials are invalid")

        if credentials.expired and credentials.refresh_token:
            request_object = GoogleAuthRequest()
            credentials.refresh(request_object)

            # Update the session with the new credentials
            request.session["google_credentials"] = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            }

        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication error",
                "message": f"Failed to create credentials object: {str(e)}",
            },
        ) from e
