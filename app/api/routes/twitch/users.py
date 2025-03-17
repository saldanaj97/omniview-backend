import base64
import json

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

import app.services.twitch.user as user

router = APIRouter()


@router.get("/following")
async def get_following(request: Request):
    token = request.cookies.get("auth_token")
    user_session = request.cookies.get("user_session")

    # Decode auth_token if it exists
    decoded_auth_token = None
    if token:
        try:
            decoded_auth_token = json.loads(base64.b64decode(token))
        except:
            decoded_auth_token = None

    # Decode user_session if it exists
    logged_in_user = None
    if user_session:
        try:
            logged_in_user = json.loads(base64.b64decode(user_session))
        except:
            logged_in_user = None

    access_token = (
        decoded_auth_token.get("access_token") if decoded_auth_token else None
    )
    user_id = logged_in_user.get("user_id") if logged_in_user else None

    following_data = await user.get_user_follows(
        access_token=access_token, user_id=user_id
    )
    return following_data["data"]
