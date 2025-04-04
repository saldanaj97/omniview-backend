from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import YOUTUBE_API_KEY

router = APIRouter()


class PlatformLoginStatus(BaseModel):
    platform: str
    loggedIn: bool


class LoginStatusResponse(BaseModel):
    data: List[PlatformLoginStatus]
    error: Optional[Dict[str, str]] = None


class PublicPlatformAccessTokenResponse(BaseModel):
    platform: str
    accessTokenAvailable: bool


class PublicAccessResponse(BaseModel):
    data: List[PublicPlatformAccessTokenResponse]
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


@router.get("/status/public", response_model=PublicAccessResponse)
async def public_check_login_status(request: Request):
    """
    Public endpoint to check which platforms have access tokens available.
    This is used for public access without requiring a session.
    """
    # For Youtube, we can check the GOOGLE_YOUTUBE_DATA_API_KEY directly since it is a static API key.
    # For Twitch and Kick, we will check the session for public credentials if available.
    try:
        platforms_status = [
            PublicPlatformAccessTokenResponse(
                platform="Twitch",
                accessTokenAvailable=bool(
                    request.session.get("twitch_public_credentials")
                ),
            ),
            PublicPlatformAccessTokenResponse(
                platform="Youtube",
                accessTokenAvailable=bool(YOUTUBE_API_KEY),
            ),
            PublicPlatformAccessTokenResponse(
                platform="Kick",
                accessTokenAvailable=bool(
                    request.session.get("kick_public_credentials")
                ),
            ),
        ]

        return PublicAccessResponse(data=platforms_status)
    except Exception as e:
        return PublicAccessResponse(data=[], error={"message": str(e)})
