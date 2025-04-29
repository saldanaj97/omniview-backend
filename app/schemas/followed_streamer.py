from typing import List, Literal

from pydantic import BaseModel


class FollowedStreamer(BaseModel):
    """
    Data model representing a followed streamer.

    Attributes:
        id (str): Unique identifier for the streamer.
        login (str): Login name of the streamer.
        display_name (str): Display name of the streamer.
        type (str): The type or category of the streamer.
        broadcaster_type (str): The broadcaster status (e.g., partner, affiliate, or standard).
        description (str): A brief description or bio of the streamer.
        profile_image_url (str): URL pointing to the streamer's profile image.
        offline_image_url (str): URL pointing to the streamer's offline image.
        view_count (int): Total number of views accumulated by the streamer.
        created_at (str): The timestamp when the streamer profile was created.
        user_id (str): Unique identifier for the user associated with the streamer.
        user_login (str): Login name of the user.
        user_name (str): Display name of the user.
        game_id (str): Unique identifier for the game currently being streamed.
        game_name (str): Name of the game currently being streamed.
        title (str): Current stream title.
        viewer_count (int): Number of viewers currently watching the stream.
        started_at (str): Timestamp when the current stream started.
        language (str): Language used in the stream.
        thumbnail_url (str): URL of the current stream's thumbnail image.
        tag_ids (List[str]): List of tag identifiers associated with the stream.
        tags (List[str]): List of tag names associated with the stream.
        is_mature (bool): Whether the stream contains mature content.
        platform (Literal["Twitch", "YouTube"]): Platform of the stream (e.g., Twitch or YouTube).
    """

    id: str
    login: str
    display_name: str
    type: str
    broadcaster_type: str
    description: str
    profile_image_url: str
    offline_image_url: str
    view_count: int
    created_at: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    tag_ids: List[str]
    tags: List[str]
    is_mature: bool
    livechat_id: str | None = None
    video_id: str | None = None
    platform: Literal["Twitch", "YouTube"]
