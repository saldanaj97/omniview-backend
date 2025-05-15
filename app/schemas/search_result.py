from typing import Optional

from pydantic import BaseModel, HttpUrl


class StreamerSearchResult(BaseModel):
    platform: str
    id: str
    username: str
    display_name: str
    profile_image_url: Optional[HttpUrl]
    broadcaster_type: Optional[str]
    is_live: Optional[bool]
    live_viewer_count: Optional[int]
