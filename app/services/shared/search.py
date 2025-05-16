import asyncio
import logging

import httpx
from fastapi import Request

from app.core.config import TWITCH_CLIENT_ID
from app.services.kick.public import fetch_profile_pictures
from app.services.shared.standardize_search import standardize_search_results
from app.utils import redis_cache
from app.utils.http_utils import ensure_session_credentials

logger = logging.getLogger(__name__)


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
        if resp.status_code != 200:
            resp.raise_for_status()
            return None

    # Kick API does not return all the data we want so we need to fetch the rest
    data = resp.json()

    # Return early if no valid data structure
    if not data.get("data") or not isinstance(data["data"], list) or not data["data"]:
        return data

    # Try to extract and enhance the first result
    first_item = data["data"][0]
    user_id = first_item.get("broadcaster_user_id")

    # Only fetch profile data if we have a user ID
    if user_id:
        # Fetch additional profile information
        profile_data = await fetch_profile_pictures(
            [user_id], client, credentials.get("access_token")
        )

        # Update data with profile information if available
        user_profile = profile_data.get(str(user_id), {})
        if user_profile:
            first_item["profile_image_url"] = user_profile.get(
                "profile_picture", first_item.get("profile_image_url")
            )
            first_item["user_name"] = user_profile.get(
                "name", first_item.get("user_name")
            )

    # Standardize the data structure and return the first item
    return first_item if first_item else None


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
        return standardize_search_results(cached)

    twitch_creds = ensure_session_credentials(
        request, "twitch_public_credentials", "Twitch"
    )
    kick_creds = ensure_session_credentials(request, "kick_public_credentials", "Kick")
    youtube_key = ensure_session_credentials(request, "", "Youtube")

    async def wrap(func, *args):
        try:
            return await func(*args)
        except Exception as exc:
            logger.error(f"Error in {func.__name__}: {exc}")
            return None

    results = await asyncio.gather(
        wrap(search_kick, kick_creds, username),
        wrap(search_twitch, twitch_creds, username),
        wrap(search_youtube, youtube_key, username),
    )

    data = {
        "twitch": results[1],
        "kick": results[0],
        "youtube": results[2],
    }
    await redis_cache.set_cache(cache_key, data, expiration=5)
    return standardize_search_results(data)
