import json
import logging

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.api.dependencies.twitch_auth import require_twitch_auth
from app.services.twitch import user
from app.utils.redis_cache import get_cache, set_cache  # added import

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/following")
async def get_following(auth_data: tuple = Depends(require_twitch_auth)):
    try:
        decoded_auth_token, logged_in_user = auth_data
        access_token = decoded_auth_token.get("access_token")
        if not access_token:
            logger.error("Missing access token in authenticated request")
            return Response(
                content=json.dumps(
                    {"error": "Missing access token", "code": "TOKEN_MISSING"}
                ),
                status_code=401,
                media_type="application/json",
            )

        user_id = logged_in_user.get("id")
        if not user_id:
            logger.error("Missing user ID in authenticated request")
            return Response(
                content=json.dumps(
                    {"error": "Missing user ID", "code": "USER_ID_MISSING"}
                ),
                status_code=401,
                media_type="application/json",
            )

        cache_key = "twitch:following"  # define cache key using user_id
        cached_data = await get_cache(cache_key)
        if cached_data:
            return Response(
                content=json.dumps({"data": cached_data}),
                status_code=200,
                media_type="application/json",
            )

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
            await set_cache(cache_key, following_data, 300)  # cache result
            return JSONResponse(
                content={"data": [user.model_dump() for user in following_data]},
                status_code=200,
            )

        # If the service returns an unexpected structure
        logger.error("Unexpected following data structure: %s", following_data)
        return JSONResponse(
            content=json.dumps(
                {
                    "error": "Unexpected response format from Twitch API",
                    "details": str(following_data),
                    "code": "UNEXPECTED_FORMAT",
                }
            ),
            status_code=502,
            media_type="application/json",
        )
    except ValueError as e:
        logger.error("Invalid data format in following data: %s", str(e))
        return Response(
            content=json.dumps(
                {
                    "error": "Invalid data format",
                    "details": str(e),
                    "code": "FORMAT_ERROR",
                }
            ),
            status_code=400,
            media_type="application/json",
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
