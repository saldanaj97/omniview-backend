import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables
load_dotenv(ENV_FILE)

# Development settings
DEBUG = os.getenv("DEBUG", "False") == "True"

# Twitch OAuth configuration
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")
TWITCH_CALLBACK_URL = os.getenv(
    "CALLBACK_URL", "http://localhost:8000/api/auth/twitch/callback"
)
SECRET_KEY = os.getenv("SECRET_KEY")

# Twitch API scopes to request
TWITCH_SCOPES = "user:read:follows"

# Google OAuth configuration
GOOGLE_CLIENT_SECRET = json.loads(os.getenv("GOOGLE_CLIENT_SECRET_JSON"))

# Google API scopes and config to request
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
GOOGLE_API_SERVICE_NAME = "youtube"
GOOGLE_API_VERSION = "v3"

# YouTube API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Kick OAuth
KICK_CLIENT_ID = os.getenv("KICK_CLIENT_ID")
KICK_CLIENT_SECRET = os.getenv("KICK_CLIENT_SECRET")
KICK_SCOPES = [
    "user:read",
    "channel:read",
    "chat:write",
    "events:subscribe",
]
