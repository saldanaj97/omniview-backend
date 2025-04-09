from typing import Dict, Tuple

from fastapi import HTTPException, Request

from app.services.twitch import auth


async def require_twitch_auth(request: Request) -> Tuple[Dict, Dict]:
    """
    Dependency that ensures a valid Twitch auth token is present.
    Attempts to refresh the token if it's expired.

    Returns:
        Tuple containing (decoded_token, user_profile)

    Raises:
        HTTPException: If authentication fails or token can't be refreshed
    """
    if "session" not in request.scope or "twitch_credentials" not in request.session:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication required",
                "message": "Please login to access this resource.",
            },
        )

    # Validate and possibly refresh the token
    is_valid = await auth.ensure_valid_token(request)
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Token expired",
                "message": "Your session has expired. Please login again.",
            },
        )

    credentials = request.session["twitch_credentials"]
    user_profile = request.session.get("twitch_user_profile", {})

    return credentials, user_profile
