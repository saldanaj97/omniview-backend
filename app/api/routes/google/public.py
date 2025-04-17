import logging

from fastapi import APIRouter

from app.services.google.public import fetch_top_streams
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/top_streams")
async def top_streams():
    """
    Get a list of current top live streams on YouTube.
    """
    cache_key = "google:public:top_streams"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data
    streams = await fetch_top_streams()
    await set_cache(cache_key, streams, 1200)
    return streams
