from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class PlatformLoginStatus(BaseModel):
    platform: str
    loggedIn: bool


class LoginStatusResponse(BaseModel):
    data: List[PlatformLoginStatus]
    error: Optional[Dict[str, str]] = None


@router.get("/status", response_model=LoginStatusResponse)
async def check_login_status(request: Request):
    """Check which platforms the user is logged into"""
    try:
        platforms_status = [
            PlatformLoginStatus(
                platform="Youtube",
                loggedIn=bool(request.session.get("google_credentials")),
            ),
            PlatformLoginStatus(
                platform="Twitch",
                loggedIn=bool(request.session.get("twitch_credentials")),
            ),
            PlatformLoginStatus(
                platform="Kick", loggedIn=bool(request.session.get("kick_credentials"))
            ),
        ]

        return LoginStatusResponse(data=platforms_status)
    except Exception as e:
        return LoginStatusResponse(data=[], error={"message": str(e)})
