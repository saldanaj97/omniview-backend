import asyncio
from typing import Dict

import httpx
from fastapi import Request

from app.core.config import TWITCH_CLIENT_ID
from app.utils.http_utils import ensure_session_credentials


async def search_kick(credentials, username: str):
    token = credentials.get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Accept": "*/*"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.kick.com/public/v1/channels",
            headers=headers,
            params={"slug": username},
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"][0] if data["data"] else None
        response.raise_for_status()


async def search_twitch(credentials, username: str):
    token = credentials.get("access_token")
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Accept": "*/*",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params={"login": username},
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"][0] if data["data"] else None
        response.raise_for_status()


async def search_youtube(credentials, username: str):
    headers = {"Accept": "*/*"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            headers=headers,
            params={
                "forUsername": username,
                "part": "id,snippet,status",
                "key": credentials,
            },
        )
        if response.status_code == 200:
            data = response.json()
            return data["items"] if data["items"] else None
        response.raise_for_status()


async def search_all_platforms(request: Request, username: str):
    # Prepare credential fetches
    twitch_credentials = ensure_session_credentials(
        request, "twitch_public_credentials", "Twitch"
    )
    kick_credentials = ensure_session_credentials(
        request, "kick_public_credentials", "Kick"
    )
    youtube_credentials = ensure_session_credentials(request, "", "Youtube")

    async with httpx.AsyncClient(timeout=5) as client:
        results = await asyncio.gather(
            search_kick(kick_credentials, username),
            search_twitch(twitch_credentials, username),
            search_youtube(youtube_credentials, username),
            return_exceptions=True,
        )

    data = {
        "kick": results[0] if not isinstance(results[0], Exception) else None,
        "twitch": results[1] if not isinstance(results[1], Exception) else None,
        "youtube": results[2] if not isinstance(results[2], Exception) else None,
    }

    # await set_cached_result(username, data)
    return data
