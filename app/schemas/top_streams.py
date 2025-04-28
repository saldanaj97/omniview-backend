from typing import Literal, Optional

from pydantic import BaseModel


class Stream(BaseModel):
    """
    Data model representing a unified stream across platforms.

    Attributes:
        id (str): Unique identifier for the stream.
        user_id (str): User or channel ID.
        user_name (str): Display name of the user or channel.
        title (str): Stream title.
        viewer_count (int): Number of viewers.
        started_at (str): ISO 8601 date string for when the stream started.
        language (str): Language of the stream.
        thumbnail_url (str): URL for the stream thumbnail.
        is_mature (bool): Whether the stream is marked as mature content.
        platform (Literal["twitch", "kick", "youtube"]): Platform of the stream.
        game_name (Optional[str]): Name of the game or category.
        stream_type (Optional[str]): Type of stream (e.g., live, vodcast).
        profile_image_url (Optional[str]): URL for the user's profile image.
    """

    id: str
    user_id: str
    user_name: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    is_mature: bool
    platform: Literal["twitch", "kick", "youtube"]
    game_name: Optional[str] = None
    stream_type: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
