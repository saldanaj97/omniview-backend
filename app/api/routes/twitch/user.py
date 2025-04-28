import json
import logging

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from idna import decode

from app.api.dependencies.twitch_auth import require_twitch_auth
from app.services.twitch import user
from app.utils.redis_cache import get_cache, set_cache  # added import

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/following")
async def get_following(auth_data: tuple = Depends(require_twitch_auth)):
    try:
        decoded_auth_token, logged_in_user = auth_data

        if not decoded_auth_token.get("access_token"):
            logger.error("Missing access token in authenticated request")
            return Response(
                content=json.dumps(
                    {"error": "Missing access token", "code": "TOKEN_MISSING"}
                ),
                status_code=401,
                media_type="application/json",
            )

        if not logged_in_user.get("id"):
            # If the user ID is not present, return an error
            logger.error("Missing user ID in authenticated request")
            return Response(
                content=json.dumps(
                    {"error": "Missing user ID", "code": "USER_ID_MISSING"}
                ),
                status_code=401,
                media_type="application/json",
            )

        # Check if the data is already cached
        cache_key = f"twitch:following:{logged_in_user.get('id')}"
        cached_data = await get_cache(cache_key)
        if cached_data:
            return Response(
                content=json.dumps({"data": cached_data}),
                status_code=200,
                media_type="application/json",
            )

        access_token = decoded_auth_token.get("access_token")
        user_id = logged_in_user.get("id")
        following_data = await user.get_user_follows(
            access_token=access_token, user_id=user_id
        )

        # If the service returns a dict with an error, propagate it
        if isinstance(following_data, dict) and "error" in following_data:
            logger.error("Twitch API error: %s", following_data)
            return Response(
                content=json.dumps(
                    {
                        "error": following_data.get("error", "Twitch API error"),
                        "details": following_data.get("message", ""),
                        "code": following_data.get("status", 400),
                    }
                ),
                status_code=following_data.get("status", 400),
                media_type="application/json",
            )

        # If the service returns a list (expected), wrap in a data key
        if isinstance(following_data, list):
            await set_cache(cache_key, following_data, 60)  # cache result
            return JSONResponse(
                content={"data": [user.model_dump() for user in following_data]},
                status_code=200,
            )

    except Exception as e:
        logger.exception("Unhandled exception in get_following")
        return Response(
            content=json.dumps(
                {
                    "error": "Failed to get following data",
                    "details": str(e),
                    "code": "INTERNAL_ERROR",
                }
            ),
            status_code=500,
            media_type="application/json",
        )
