import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# Load environment variables
load_dotenv(ENV_FILE)

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
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CALLBACK_URL = os.getenv(
    "GOOGLE_CALLBACK_URL", "http://localhost:8000/api/auth/google/callback"
)
