import base64
import json
from typing import Dict, Tuple

from fastapi import HTTPException, Request


async def require_twitch_auth(request: Request) -> Tuple[Dict, Dict]:
    """
    Dependency that checks for Twitch authentication in the session.
    Returns a tuple of (decoded_auth_token, logged_in_user) if authenticated.
    Raises HTTPException with 401 status code if not authenticated.
    """
    user_session = request.session.get("twitch_user_profile")
    token = request.session.get("twitch_credentials")

    if not token or not user_session:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "User not authenticated",
                "message": "Please login to access this resource.",
            },
        )

    try:
        # Check if values are already dictionaries
        if isinstance(token, dict):
            decoded_auth_token = token
        else:
            decoded_auth_token = json.loads(base64.b64decode(token))

        if isinstance(user_session, dict):
            logged_in_user = user_session
        else:
            logged_in_user = json.loads(base64.b64decode(user_session))
        return decoded_auth_token, logged_in_user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication error",
                "message": f"Failed to decode authentication data: {str(e)}",
            },
        ) from e
