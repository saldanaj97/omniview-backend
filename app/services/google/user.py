import asyncio
import json
import re

import httpx
from bs4 import BeautifulSoup, Tag

from app.core.config import YOUTUBE_API_KEY
from app.schemas.followed_streamer import FollowedStreamer


async def check_multiple_channels_live_status(channel_ids):
    """
    Checks the live status of multiple YouTube channels in parallel.

    This asynchronous function efficiently processes a batch of channel IDs using a single
    shared HTTP session with connection pooling. It leverages asyncio to execute all
    requests concurrently.

    Uses connection pooling with a limit of 50 concurrent connections and a 15-second timeout.
    """
    results = {}

    # Use a single shared client for all requests
    limits = httpx.Limits(max_connections=50)
    timeout = httpx.Timeout(timeout=15.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        # Create tasks for all channels in one go
        tasks = [
            check_channel_live_status_with_session(channel_id, client)
            for channel_id in channel_ids
        ]

        # Process all channels at once for maximum parallelism
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update results dictionary
        for channel_id, result in zip(channel_ids, batch_results):
            if isinstance(result, Exception):
                # Handle any exceptions
                results[channel_id] = {
                    "cid": channel_id,
                    "live": False,
                    "error": str(result),
                }
            else:
                results[channel_id] = result

    return results


async def check_channel_live_status_with_session(
    channel_id: str, client: httpx.AsyncClient
):
    """Check if a YouTube channel is currently live streaming using provided session"""
    # Initialize with default values
    channel_data = {"cid": channel_id, "live": False, "configured": False}

    try:
        # 1. Check if channel has configured livestream
        canonical_url = await get_canonical_url(channel_id, client)
        if not canonical_url or "/watch?v=" not in canonical_url:
            return channel_data

        channel_data["configured"] = True

        # 2. Extract video ID and fetch details
        video_id = extract_video_id(canonical_url)
        if not video_id:
            return channel_data

        channel_data["vid"] = video_id

        # 3. Get video details from YouTube API
        video_data = await fetch_video_details(video_id, client)
        if "error" in video_data or not video_data.get("items"):
            return (
                {"error": video_data.get("error")}
                if "error" in video_data
                else channel_data
            )

        # 4. Extract and add video metadata to result
        return extract_video_metadata(video_data["items"][0], channel_data)

    except Exception as e:
        return {"cid": channel_id, "live": False, "error": str(e)}


async def get_canonical_url(channel_id, client):
    """
    Asynchronously retrieves the canonical URL for a YouTube channel's live stream.

    This function makes an HTTP GET request to the YouTube channel's live page
    and parses the HTML response to extract the canonical URL from the metadata.
    """
    response = await client.get(
        f"https://www.youtube.com/channel/{channel_id}/live", timeout=10.0
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    canonical_url_tag = soup.find("link", rel="canonical")
    if canonical_url_tag and isinstance(canonical_url_tag, Tag):
        return canonical_url_tag.get("href")
    return None


def extract_video_id(url):
    """
    Extract the video ID from a YouTube video URL.
    """
    match = re.search(r"(?<==).*", url)
    return match.group(0) if match else None


async def fetch_video_details(video_id, client):
    """
    Asynchronously fetches video details from the YouTube API.

    This function makes a GET request to the YouTube API to retrieve specific
    details (liveStreamingDetails and snippet) for a given video ID.
    """
    youtube_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&part=liveStreamingDetails,snippet&id={video_id}"
    response = await client.get(youtube_url, timeout=10.0)
    return response.json()


def extract_video_metadata(item, channel_data):
    """
    Extracts and processes metadata from a YouTube video item.

    This function extracts relevant metadata from a YouTube video API response item
    and adds it to the provided channel_data dictionary. Extracted metadata includes
    the video title, best available thumbnail URL, and livestreaming details if available.
    """
    # Add title
    channel_data["title"] = item["snippet"].get("title", None)
    channel_data["language"] = item["snippet"].get("defaultAudioLanguage", None)

    # Select best available thumbnail
    thumbnails = item["snippet"]["thumbnails"]
    for quality in ["standard", "high", "medium", "default"]:
        if quality in thumbnails:
            channel_data["thumbnail"] = thumbnails[quality]["url"]
            break

    # Extract livestream details
    if "liveStreamingDetails" in item:
        live_details = item["liveStreamingDetails"]
        if "scheduledStartTime" in live_details:
            channel_data["scheduledStartTime"] = live_details["scheduledStartTime"]

        channel_data["live"] = "actualStartTime" in live_details
        if channel_data["live"]:
            channel_data["actualStartTime"] = live_details["actualStartTime"]
            channel_data["viewer_count"] = live_details.get("concurrentViewers", 0)
            channel_data["live_chat_id"] = live_details.get("activeLiveChatId", None)

    return channel_data


async def fetch_all_subscriptions(youtube):
    """Fetch all pages of user subscriptions"""
    # Get first page
    subscriptions = (
        youtube.subscriptions()
        .list(part="snippet", mine=True, maxResults=50, order="alphabetical")
        .execute()
    )

    all_items = subscriptions["items"].copy()
    next_page_token = subscriptions.get("nextPageToken")

    # Fetch remaining pages
    while next_page_token:
        next_page = (
            youtube.subscriptions()
            .list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=next_page_token,
                order="alphabetical",
            )
            .execute()
        )

        all_items.extend(next_page["items"])
        next_page_token = next_page.get("nextPageToken")

    return all_items


async def check_all_channels_live_status(subscriptions):
    """Check live status for all subscribed channels in parallel batches"""
    tasks = []

    # Group subscriptions into batches of 50 channels
    channel_batches = []
    current_batch = []

    for subscription in subscriptions:
        current_batch.append(subscription["snippet"]["resourceId"]["channelId"])

        if len(current_batch) == 50:  # Process in batches of 50
            channel_batches.append(current_batch)
            current_batch = []

    # Add any remaining channels
    if current_batch:
        channel_batches.append(current_batch)

    # Create tasks for all batches
    for batch in channel_batches:
        tasks.append(asyncio.create_task(check_multiple_channels_live_status(batch)))

    # Wait for all results
    results = await asyncio.gather(*tasks)

    # Combine all results
    live_statuses = {}
    for result in results:
        live_statuses.update(result)

    return live_statuses


def enrich_and_filter_live_subscriptions(subscriptions, live_statuses):
    """Add live status info to subscriptions, filter for live channels, and standardize data"""
    for subscription in subscriptions:
        channel_id = subscription["snippet"]["resourceId"]["channelId"]
        subscription["livestream_info"] = live_statuses.get(channel_id, {"live": False})
        subscription["livestream_info"]["live_chat_id"] = live_statuses.get(
            channel_id, {}
        ).get("live_chat_id")
    live_subs = [
        subscription
        for subscription in subscriptions
        if subscription["livestream_info"].get("live")
    ]
    standardized_followed_streamer_data = [
        standardize_data(subscription) for subscription in live_subs
    ]
    return standardized_followed_streamer_data


def standardize_data(subscription) -> FollowedStreamer:
    """Converts a subscription with livestream info to the FollowedStreamer format."""
    ls = subscription.get("livestream_info", {})
    snippet = subscription.get("snippet", {})
    thumbnails = snippet.get("thumbnails", {})
    default_thumb = thumbnails.get("default", {}).get("url", "")
    high_thumb = thumbnails.get("high", {}).get("url", default_thumb)

    return FollowedStreamer(
        id=snippet.get("resourceId", {}).get("channelId", ""),
        login=snippet.get("customUrl", ""),
        display_name=snippet.get("title", ""),
        type="",
        broadcaster_type="",
        description=snippet.get("description", ""),
        profile_image_url=default_thumb,
        offline_image_url=high_thumb,
        view_count=ls.get("viewer_count", 0),
        created_at="",
        user_id=snippet.get("resourceId", {}).get("channelId", ""),
        user_login=snippet.get("customUrl", ""),
        user_name=snippet.get("title", ""),
        game_id="",
        game_name="Youtube Content",
        title=ls.get("title", snippet.get("title", "")),
        viewer_count=ls.get("viewer_count", 0),
        started_at=ls.get("actualStartTime", ls.get("scheduledStartTime", "")),
        language=ls.get("language") or "",  # fallback to empty string if None
        thumbnail_url=ls.get("thumbnail", default_thumb),
        tag_ids=[],
        tags=[],
        is_mature=False,
        livechat_id=ls.get("live_chat_id", None),
        video_id=ls.get("vid", None),
        platform="youtube",
    )
