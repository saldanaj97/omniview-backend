import httpx

from app.core.config import YOUTUBE_API_KEY
from app.utils.http_utils import check_youtube_response_status


# Helper function to standardize YouTube streams
def standardize_youtube_stream_data(item: dict, extra: dict) -> dict:
    # Extract data from the search response
    video_id = item["id"]["videoId"]
    snippet = item.get("snippet", {})
    live_details = extra.get("liveStreamingDetails", {})
    snippet_extra = extra.get("snippet", {})

    return {
        "id": video_id,
        "user_id": snippet.get("channelId", ""),
        "user_name": snippet.get("channelTitle", ""),
        "title": snippet.get("title", ""),
        "viewer_count": (
            int(live_details.get("concurrentViewers", 0))
            if live_details.get("concurrentViewers")
            else 0
        ),
        "started_at": snippet.get("publishedAt", ""),
        "language": (
            snippet_extra.get("defaultAudioLanguage", "")
            if snippet_extra.get("defaultAudioLanguage")
            else ""
        ),
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "is_mature": False,
        "platform": "youtube",
        "stream_type": "live",
        "game_name": None,  # added for uniformity with other platforms
    }


async def get_livestream_details(video_id: str, client: httpx.AsyncClient) -> dict:
    viewer_count_url = (
        f"https://youtube.googleapis.com/youtube/v3/videos?"
        f"part=snippet,liveStreamingDetails&id={video_id}&key={YOUTUBE_API_KEY}"
    )
    viewer_count_response = await client.get(viewer_count_url)
    check_youtube_response_status(
        viewer_count_response, "YouTube livestream details error"
    )
    extra_json = viewer_count_response.json()
    if extra_json.get("items"):
        return extra_json["items"][0]
    return {}


async def fetch_top_streams(credentials):
    url = "https://youtube.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "eventType": "live",
        "maxResults": 10,
        "type": "video",
        "order": "viewCount",
        "regionCode": "US",
        "key": credentials,
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        check_youtube_response_status(response, "YouTube search error")
        response_data = response.json()
        transformed_data = {"data": []}
        for item in response_data.get("items", []):
            video_id = item["id"]["videoId"]
            extra_data = await get_livestream_details(video_id, client)
            standardized_stream_data = standardize_youtube_stream_data(item, extra_data)
            transformed_data["data"].append(standardized_stream_data)
    return transformed_data
