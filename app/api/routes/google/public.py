import logging

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import YOUTUBE_API_KEY
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/top_streams")
async def top_streams():
    """
    Get a list of current top live streams on YouTube.
    Uses the YouTube Data API with the API key from configuration.
    """
    # Cache key for this endpoint
    cache_key = "google:public:top_streams"

    # Try to get from cache first
    print("Attempting to fetch YouTube top streams cache -> ", cache_key)
    cached_data = await get_cache(cache_key)
    if cached_data:
        print("Cache hit for YouTube top streams")
        return cached_data

    print("Cache miss - fetching live top streams from YouTube API")

    # Check if API key is configured
    if not YOUTUBE_API_KEY:
        raise HTTPException(status_code=500, detail="YouTube API key not configured")

    try:
        # Prepare the URL with query parameters
        url = "https://youtube.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "eventType": "live",
            "maxResults": 10,
            "type": "video",
            "order": "viewCount",
            "regionCode": "US",
            "key": YOUTUBE_API_KEY,
        }
        headers = {"Accept": "application/json"}

        # Make the request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

            # Check for successful response
            if response.status_code != 200:
                logger.error(
                    "YouTube API error: %d - %s", response.status_code, response.text
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"YouTube API error: {response.text}",
                )

            # Parse the JSON response
            response_data = response.json()

            # Transform the response to match expected format
            transformed_data = {
                "data": [
                    {
                        "id": item["id"]["videoId"],
                        "user_id": item["snippet"]["channelId"],
                        "user_login": item["snippet"]["channelTitle"],
                        "user_name": item["snippet"]["channelTitle"],
                        "type": "live",
                        "title": item["snippet"]["title"],
                        "viewer_count": 0,  # YouTube API doesn't provide viewer count in this endpoint
                        "started_at": item["snippet"]["publishedAt"],
                        "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
                        "platform": "YouTube",
                    }
                    for item in response_data.get("items", [])
                ]
            }

            # Get the viewer count, live chat ID and language
            for livestream in transformed_data["data"]:
                video_id = livestream["id"]
                viewer_count_url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2CliveStreamingDetails&id={video_id}&key={YOUTUBE_API_KEY}"
                viewer_count_response = await client.get(viewer_count_url)
                if viewer_count_response.status_code == 200:
                    viewer_count_data = viewer_count_response.json()
                    if viewer_count_data.get("items"):
                        livestream["viewer_count"] = (
                            viewer_count_data["items"][0]
                            .get("liveStreamingDetails", {})
                            .get("concurrentViewers", 0)
                        )
                        livestream["live_chat_id"] = (
                            viewer_count_data["items"][0]
                            .get("liveStreamingDetails", {})
                            .get("activeLiveChatId", None)
                        )
                        livestream["language"] = viewer_count_data["items"][0][
                            "snippet"
                        ].get("defaultAudioLanguage", None)

                else:
                    logger.error(
                        "Failed to fetch viewer count for video ID %s: %d - %s",
                        video_id,
                        viewer_count_response.status_code,
                        viewer_count_response.text,
                    )
                    livestream["viewer_count"] = 0

            # Cache for 20 minutes (1200 seconds) to stay within the YouTube API quota of 7,500 units per day
            await set_cache(cache_key, transformed_data, 1200)
            return transformed_data

    except Exception as e:
        logger.error("Failed to fetch YouTube top streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
