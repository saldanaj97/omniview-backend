import json

from fastapi import APIRouter, Depends, Request, Response

import app.services.twitch.user as user
from app.api.dependencies.twitch_auth import require_twitch_auth

router = APIRouter()


@router.get("/following")
async def get_following(
    request: Request, auth_data: tuple = Depends(require_twitch_auth)
):
    following_data = {}
    try:
        decoded_auth_token, logged_in_user = auth_data
        access_token = decoded_auth_token.get("access_token")
        user_id = logged_in_user.get("id")
        following_data = await user.get_user_follows(
            access_token=access_token, user_id=user_id
        )
        return Response(content=json.dumps(following_data["data"]))
    except Exception as e:
        return Response(
            content=json.dumps(
                {"error": "Failed to get following data", "message": str(e)}
            ),
            status_code=500,
        )
