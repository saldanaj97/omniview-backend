import logging

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/top_streams")
async def top_streams(request: Request):
    """
    Endpoint to get top streams from Kick.
    """
    # Cache key for this endpoint
    cache_key = "kick:public:top_streams"

    # Try to get from cache first
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    if not request.session.get("kick_public_credentials"):
        logger.error("No Kick credentials found in session")
        raise HTTPException(
            status_code=401,
            detail="No access token found for Kick.",
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.kick.com/public/v1/livestreams",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": (
                        f"Bearer {request.session['kick_public_credentials'].get('access_token')}"
                    ),
                },
            )

        if response.status_code != 200:
            logger.error("Kick API error: %d - %s", response.status_code, response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve top streams: {response.text}",
            )
        response_data = response.json()

        # Cache for 2 minutes (120 seconds) since stream data changes frequently
        success = await set_cache(cache_key, response_data, 120)
        return response_data

    except Exception as e:
        logger.exception("Error fetching Kick streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
