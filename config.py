import os

from dotenv import load_dotenv

load_dotenv()

# Twitch OAuth configuration
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET = os.getenv("TWITCH_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:8000/auth/twitch/callback")
SECRET_KEY = os.getenv("SECRET_KEY")

# API scopes to request
TWITCH_SCOPES = "user:read:follows"
