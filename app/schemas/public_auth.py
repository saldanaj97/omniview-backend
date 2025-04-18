from typing import Dict, List, Optional

from pydantic import BaseModel


class PlatformLoginStatus(BaseModel):
    """Represents the login status for a specific platform."""

    platform: str
    loggedIn: bool


class LoginStatusResponse(BaseModel):
    """Response model containing a list of platform login statuses and optional error information."""

    data: List[PlatformLoginStatus]
    error: Optional[Dict[str, str]] = None


class PublicPlatformAccessTokenResponse(BaseModel):
    """Represents the access token availability for a specific public platform."""

    platform: str
    accessTokenAvailable: bool


class PublicAccessResponse(BaseModel):
    """Response model containing a list of public access token responses and optional error information."""

    data: List[PublicPlatformAccessTokenResponse]
    error: Optional[Dict[str, str]] = None
