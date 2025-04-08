import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth_status, debug
from app.api.routes.google import auth as google_auth
from app.api.routes.google import subscriptions as google_subscriptions
from app.api.routes.kick import auth as kick_auth
from app.api.routes.kick import public as kick_public
from app.api.routes.twitch import auth as twitch_auth
from app.api.routes.twitch import public as twitch_public
from app.api.routes.twitch import users as twitch_users
from app.core.config import SECRET_KEY
from app.core.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=False,  # Set to True in production with HTTPS
    same_site="lax",
)

# For development only - disable in production
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Routers
# Global Routes
app.include_router(auth_status.router, prefix="/api/auth", tags=["authentication"])

# Debug routes (only in debug mode)
if os.getenv("DEBUG", "False") == "True":
    logger.info("Debug mode enabled - registering debug endpoints")
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

# Twitch API routes
app.include_router(twitch_auth.router, prefix="/api/twitch", tags=["authentication"])
app.include_router(twitch_users.router, prefix="/api/twitch", tags=["users"])
app.include_router(twitch_public.router, prefix="/api/twitch/public", tags=["public"])

# Google API routes
app.include_router(google_auth.router, prefix="/api/google", tags=["authentication"])
app.include_router(google_subscriptions.router, prefix="/api/google", tags=["users"])
# app.include_router(google_public.router, prefix="/api/public/google", tags=["public"])

# Kick API routes
app.include_router(kick_auth.router, prefix="/api/kick", tags=["authentication"])
app.include_router(kick_public.router, prefix="/api/kick/public", tags=["public"])

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
