import json
import logging

from fastapi import APIRouter, Depends, Response

from app.api.dependencies.twitch_auth import require_twitch_auth
from app.services.twitch import user

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

        following_data = await user.get_user_follows(
            access_token=access_token, user_id=user_id
        )

        if not following_data:
            logger.error("No response from Twitch API while fetching user follows")
            return Response(
                content=json.dumps(
                    {"error": "No response from Twitch API", "code": "TWITCH_API_ERROR"}
                ),
                status_code=502,
                media_type="application/json",
            )

        if "data" not in following_data or "error" in following_data:
            logger.error("Error in Twitch API response: %s", following_data)
            return Response(
                content=json.dumps(following_data),
                status_code=following_data.get("status", 400),
                media_type="application/json",
            )

        return Response(
            content=json.dumps(following_data["data"]), media_type="application/json"
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
        return Response(
            content=json.dumps(
                {"error": "Failed to get following data", "details": str(e)}
            ),
            status_code=500,
            media_type="application/json",
        )
