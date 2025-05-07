import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import debug
from app.api.routes.google import auth as google_auth
from app.api.routes.google import public as google_public
from app.api.routes.google import user as google_subscriptions
from app.api.routes.kick import auth as kick_auth
from app.api.routes.kick import public as kick_public
from app.api.routes.shared import following, public_auth, top_streams
from app.api.routes.twitch import auth as twitch_auth
from app.api.routes.twitch import public as twitch_public
from app.api.routes.twitch import user as twitch_users
from app.core.config import SECRET_KEY
from app.core.redis_client import redis_client
from app.utils.logging import configure_logging

# Ensure SECRET_KEY is not None
assert SECRET_KEY is not None, "SECRET_KEY must be defined"

# Configure logging with our new system
debug_mode = os.getenv("DEBUG", "False") == "True"

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OmniView Backend",
    description="OmniView Backend API",
    version="0.1.0",
)

# Test Redis connection
try:
    redis_client.ping()
    logger.info("Redis connection successful")
except Exception as e:
    logger.error("Redis connection failed: %s", str(e))
    raise

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://omniview-frontend-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,  # Set to True in production with HTTPS
    same_site="lax",  # Set to "lax" or "strict" in production
)


# Debug Mode
if debug_mode:
    logger.info("Debug mode enabled - registering debug endpoints")

    # Configure logging for debug mode
    LOG_LEVEL = "DEBUG" if debug_mode else "INFO"
    configure_logging(log_level=LOG_LEVEL)

    # Used to allow insecure transport for OAuth per the youtube data api docs
    # For development only - disable in production
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Debug routes
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

# Routers

# Global Routes
app.include_router(public_auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(following.router, prefix="/api", tags=["shared"])
app.include_router(top_streams.router, prefix="/api", tags=["shared"])

# Twitch API routes
app.include_router(twitch_auth.router, prefix="/api/twitch", tags=["authentication"])
app.include_router(twitch_users.router, prefix="/api/twitch", tags=["users"])
app.include_router(twitch_public.router, prefix="/api/twitch/public", tags=["public"])

# Google API routes
app.include_router(google_auth.router, prefix="/api/google", tags=["authentication"])
app.include_router(google_subscriptions.router, prefix="/api/google", tags=["users"])
app.include_router(google_public.router, prefix="/api/google/public", tags=["public"])

# Kick API routes
app.include_router(kick_auth.router, prefix="/api/kick", tags=["authentication"])
app.include_router(kick_public.router, prefix="/api/kick/public", tags=["public"])

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=2,
    )
