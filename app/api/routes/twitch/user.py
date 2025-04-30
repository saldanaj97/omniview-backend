import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.api.dependencies.twitch_auth import require_twitch_auth
from app.schemas.followed_streamer import FollowedStreamer
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
            raise HTTPException(
                status_code=401,
                detail={"error": "Missing access token", "code": "TOKEN_MISSING"},
            )

        if not logged_in_user.get("id"):
            logger.error("Missing user ID in authenticated request")
            raise HTTPException(
                status_code=401,
                detail={"error": "Missing user ID", "code": "USER_ID_MISSING"},
            )

        # Check if the data is already cached
        cache_key = f"twitch:following:{logged_in_user.get('id')}"
        cached_data = await get_cache(cache_key)

        # Deserialize cached response into FollowedStreamer models
        if cached_data:
            return {
                "data": [FollowedStreamer.model_validate(item) for item in cached_data]
            }

        access_token = decoded_auth_token.get("access_token")
        user_id = logged_in_user.get("id")
        following_data = await user.get_user_follows(
            access_token=access_token, user_id=user_id
        )

        # Cache the serializable data for 60 seconds
        await set_cache(
            cache_key, [streamer.model_dump() for streamer in following_data], 60
        )

        return {"data": following_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled exception in get_following")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get following data",
                "details": str(e),
                "code": "INTERNAL_ERROR",
            },
        )
