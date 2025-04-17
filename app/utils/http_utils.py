from fastapi import HTTPException, Request

from app.core.config import YOUTUBE_API_KEY


def check_kick_response_status(response, context: str = "Kick API error"):
    """
    Utility to check Kick API response status and raise a FastAPI HTTPException with details.
    """
    if response.status_code != 200:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{context}: {error_detail}",
        )


def check_youtube_response_status(response, context: str = "YouTube API error"):
    """
    Utility to check YouTube API response status and raise a FastAPI HTTPException with details.
    """
    if response.status_code != 200:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{context}: {error_detail}",
        )


def check_twitch_response_status(response, context: str = "Twitch API error"):
    """
    Utility to check HTTPX response status and raise a FastAPI HTTPException with details.
    """
    if response.status_code != 200:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{context}: {error_detail}",
        )


def ensure_session_credentials(request: Request, name: str, platform: str):
    """
    Ensures public credentials are available in the session.
    Returns the credentials if available; otherwise raises HTTPException.
    """
    # If the platform is YouTube, but the API key is not configured, raise an exception
    if platform == "Youtube" and YOUTUBE_API_KEY is None:
        raise HTTPException(
            status_code=401,
            detail="YouTube API key is not configured.",
        )

    # If the platform is YouTube, return the API key directly
    if platform == "Youtube":
        return YOUTUBE_API_KEY

    # For other platforms, check the session for credentials
    credentials = request.session.get(name)
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail=f"No access token found for {platform}.",
        )
    return credentials
