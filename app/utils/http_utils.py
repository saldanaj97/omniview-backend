from fastapi import HTTPException, Request


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


def ensure_session_credentials(request: Request, name: str, platform: str) -> dict:
    """
    Ensures public credentials are available in the session.
    Returns the credentials if available; otherwise raises HTTPException.
    """
    credentials = request.session.get(name)
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail=f"No access token found for {platform}.",
        )
    return credentials
