import asyncio

import httpx
from fastapi import Request

from app.core.config import TWITCH_CLIENT_ID
from app.utils import redis_cache
from app.utils.http_utils import ensure_session_credentials


async def search_kick(credentials, username: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {credentials.get('access_token')}",
        "Accept": "*/*",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.kick.com/public/v1/channels",
            headers=headers,
            params={"slug": username},
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["data"][0] if data.get("data") else None
        resp.raise_for_status()


async def search_twitch(credentials, username: str) -> dict | None:
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {credentials.get('access_token')}",
        "Accept": "*/*",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params={"login": username},
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["data"][0] if data.get("data") else None
        resp.raise_for_status()


async def search_youtube(api_key: str, username: str) -> dict | None:
    headers = {"Accept": "*/*"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            headers=headers,
            params={
                "forHandle": username,
                "part": "id,snippet",
                "key": api_key,
                "maxResults": 10,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items") or None
        resp.raise_for_status()


async def search_all_platforms(request: Request, username: str) -> dict:
    cache_key = f"search:all:{username.lower()}"
    cached = await redis_cache.get_cache(cache_key)
    if cached is not None:
        return cached

    twitch_creds = ensure_session_credentials(
        request, "twitch_public_credentials", "Twitch"
    )
    kick_creds = ensure_session_credentials(request, "kick_public_credentials", "Kick")
    youtube_key = ensure_session_credentials(request, "", "Youtube")

    async def wrap(func, *args):
        try:
            return await func(*args)
        except Exception:
            return None

    results = await asyncio.gather(
        wrap(search_kick, kick_creds, username),
        wrap(search_twitch, twitch_creds, username),
        wrap(search_youtube, youtube_key, username),
    )

    data = {"kick": results[0], "twitch": results[1], "youtube": results[2]}
    await redis_cache.set_cache(cache_key, data, expiration=300)
    return data
