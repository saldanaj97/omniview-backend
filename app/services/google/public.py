from typing import List, Optional

import httpx

from app.core.config import YOUTUBE_API_KEY
from app.utils.http_utils import check_youtube_response_status


# Helper function to convert raw YouTube data into unified Stream schema
def standardize_youtube_stream_data(
    item: dict, extra: dict, channel_snippet: Optional[dict] = None
) -> dict:
    """
    Convert raw YouTube stream item and details into unified Stream schema.
    """
    # Ensure channel_snippet default
    if channel_snippet is None:
        channel_snippet = {}
    # Extract data from the search response
    video_id = item["id"]["videoId"]
    snippet = item.get("snippet", {})
    live_details = extra.get("liveStreamingDetails", {})
    snippet_extra = extra.get("snippet", {})
    profile_image_url = (
        channel_snippet.get("thumbnails", {}).get("default", {}).get("url", "")
    )

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
        "language": snippet_extra.get("defaultAudioLanguage", ""),
        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "is_mature": False,
        "platform": "youtube",
        "game_name": None,
        "stream_type": "live",
        "profile_image_url": profile_image_url,
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
        "key": credentials,
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        check_youtube_response_status(response, "YouTube search error")
        response_data = response.json()

        items = response_data.get("items", [])
        if not items:
            return {"data": []}

        # Batch fetch video details
        video_ids = [item["id"]["videoId"] for item in items]
        videos_url = "https://youtube.googleapis.com/youtube/v3/videos"
        videos_params = {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(video_ids),
            "key": credentials,
        }
        videos_resp = await client.get(
            videos_url, params=videos_params, headers=headers
        )
        check_youtube_response_status(videos_resp, "YouTube videos details error")
        details_items = videos_resp.json().get("items", [])
        details_map = {d["id"]: d for d in details_items}

        # Batch fetch channel snippets for profile images
        channel_ids = {d.get("snippet", {}).get("channelId") for d in details_items}
        channels_url = "https://youtube.googleapis.com/youtube/v3/channels"
        channels_params = {
            "part": "snippet",
            "id": ",".join(channel_ids),
            "key": credentials,
        }
        channels_resp = await client.get(
            channels_url, params=channels_params, headers=headers
        )
        check_youtube_response_status(channels_resp, "YouTube channels error")
        channel_items = channels_resp.json().get("items", [])
        channel_map = {c["id"]: c.get("snippet", {}) for c in channel_items}

        unified: List[dict] = []
        for item in items:
            vid = item["id"]["videoId"]
            extra = details_map.get(vid, {})
            chan_snip = channel_map.get(
                extra.get("snippet", {}).get("channelId", ""), {}
            )
            unified.append(standardize_youtube_stream_data(item, extra, chan_snip))

    return {"data": unified}
