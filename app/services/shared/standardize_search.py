from typing import List, Optional, Union

from pydantic import HttpUrl

from app.schemas.search_result import StreamerSearchResult


def standardize_twitch_search_result(
    twitch_data: dict,
) -> Optional[StreamerSearchResult]:
    """
    Converts a Twitch user search result to a standardized StreamerSearchResult.

    Args:
        twitch_data: A dictionary containing Twitch user data

    Returns:
        A StreamerSearchResult object, or None if the input is invalid
    """
    if not twitch_data:
        return None

    return StreamerSearchResult(
        platform="twitch",
        id=twitch_data.get("id", ""),
        username=twitch_data.get("login", ""),
        display_name=twitch_data.get("display_name", ""),
        profile_image_url=twitch_data.get("profile_image_url"),
        broadcaster_type=twitch_data.get("broadcaster_type"),
        is_live=None,  # Twitch search doesn't include this by default
        live_viewer_count=None,  # Twitch search doesn't include this by default
    )


def standardize_kick_search_result(kick_data: dict) -> Optional[StreamerSearchResult]:
    """
    Converts a Kick user search result to a standardized StreamerSearchResult.

    Args:
        kick_data: A dictionary containing Kick user data

    Returns:
        A StreamerSearchResult object, or None if the input is invalid
    """
    if not kick_data:
        return None

    # Check if user has a stream and if it's live
    is_live = False
    live_viewer_count = None
    if kick_data.get("stream"):
        is_live = kick_data["stream"].get("is_live", False)
        live_viewer_count = kick_data["stream"].get("viewer_count", 0)

    return StreamerSearchResult(
        platform="kick",
        id=str(kick_data.get("broadcaster_user_id", "")),
        username=kick_data.get("slug", ""),
        display_name=kick_data.get("user_name", ""),
        profile_image_url=kick_data.get("profile_image_url"),
        broadcaster_type=None,  # Kick doesn't have a direct equivalent
        is_live=is_live,
        live_viewer_count=live_viewer_count,
    )


def standardize_youtube_search_result(
    youtube_data: Union[dict, List[dict]],
) -> Optional[StreamerSearchResult]:
    """
    Converts a YouTube channel search result to a standardized StreamerSearchResult.

    Args:
        youtube_data: A dictionary or list of dictionaries containing YouTube channel data

    Returns:
        A StreamerSearchResult object, or None if the input is invalid
    """
    if not youtube_data:
        return None

    # If youtube_data is a list, take the first item
    if isinstance(youtube_data, list) and youtube_data:
        yt_item = youtube_data[0]
    else:
        yt_item = youtube_data

    # Extract snippet if it exists
    snippet = yt_item.get("snippet", {})

    # Get the best available thumbnail
    profile_image_url = None
    if thumbnails := snippet.get("thumbnails", {}):
        # Try to get the highest resolution thumbnail available
        for size in ["high", "medium", "default"]:
            if size in thumbnails and "url" in thumbnails[size]:
                profile_image_url = thumbnails[size]["url"]
                break

    return StreamerSearchResult(
        platform="youtube",
        id=yt_item.get("id", ""),
        username=snippet.get("customUrl", "").replace("@", ""),
        display_name=snippet.get("title", ""),
        profile_image_url=profile_image_url,
        broadcaster_type=None,  # YouTube doesn't have a direct equivalent
        is_live=None,  # YouTube search doesn't include this by default
        live_viewer_count=None,  # YouTube search doesn't include this by default
    )


def standardize_search_results(data) -> dict:
    """
    Converts platform-specific search results to standardized StreamerSearchResult objects.

    Args:
        data: A dictionary or list with platform-specific search results

    Returns:
        A dictionary with keys for each platform and values as StreamerSearchResult objects
    """
    # Ensure we're working with a dictionary
    if not isinstance(data, dict):
        if isinstance(data, list):
            # If it's a list, we can't process it properly, return empty results
            return {"twitch": None, "kick": None, "youtube": None}
        # If it's something else, return empty results
        return {"twitch": None, "kick": None, "youtube": None}

    result = {}

    if twitch_data := data.get("twitch"):
        result["twitch"] = standardize_twitch_search_result(twitch_data)
    else:
        result["twitch"] = None

    if kick_data := data.get("kick"):
        result["kick"] = standardize_kick_search_result(kick_data)
    else:
        result["kick"] = None

    if youtube_data := data.get("youtube"):
        result["youtube"] = standardize_youtube_search_result(youtube_data)
    else:
        result["youtube"] = None

    return result
