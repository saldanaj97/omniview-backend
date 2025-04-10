import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.api.routes.kick.auth import kick_public_token
from app.api.routes.twitch.auth import twitch_public_token
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

    If Twitch or Kick tokens are not available, this endpoint will attempt
    to generate them using the respective public token endpoints.
    """
    try:
        # Check if Twitch public token is available, if not, try to generate it
        twitch_token_available = bool(request.session.get("twitch_public_credentials"))
        if not twitch_token_available:
            try:
                credentials = await twitch_public_token(request)
                request.session["twitch_public_credentials"] = credentials
                twitch_token_available = bool(
                    request.session.get("twitch_public_credentials")
                )
            except Exception as e:
                logging.error("Failed to generate Twitch public token: %s", str(e))

        # Check if Kick public token is available, if not, try to generate it
        kick_token_available = bool(request.session.get("kick_public_credentials"))
        if not kick_token_available:
            try:
                credentials = await kick_public_token(request)
                request.session["kick_public_credentials"] = credentials
                kick_token_available = bool(
                    request.session.get("kick_public_credentials")
                )
            except Exception as e:
                logging.error("Failed to generate Kick public token: %s", str(e))

        # For Youtube, we check the API key directly since it's static
        youtube_token_available = bool(YOUTUBE_API_KEY)

        platforms_status = [
            PublicPlatformAccessTokenResponse(
                platform="Twitch",
                accessTokenAvailable=twitch_token_available,
            ),
            PublicPlatformAccessTokenResponse(
                platform="Youtube",
                accessTokenAvailable=youtube_token_available,
            ),
            PublicPlatformAccessTokenResponse(
                platform="Kick",
                accessTokenAvailable=kick_token_available,
            ),
        ]

        return PublicAccessResponse(data=platforms_status)
    except Exception as e:
        return PublicAccessResponse(data=[], error={"message": str(e)})
