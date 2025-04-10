import httpx
from fastapi import HTTPException

from app.core.config import KICK_CLIENT_ID, KICK_CLIENT_SECRET


async def get_kick_public_access_token():
    """
    Get an app access token using the client credentials grant flow.
    This is useful for server-to-server requests without user context.
    """
    params = {
        "grant_type": "client_credentials",
        "client_id": KICK_CLIENT_ID,
        "client_secret": KICK_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://id.kick.com/oauth/token", data=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get kick public access token: {response.text}",
        )

    public_token = response.json()
    return public_token
