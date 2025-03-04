from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

import app.services.user as user

router = APIRouter()


@router.get("/following")
async def get_following(request: Request):
    logged_in_user = request.session.get("user")
    if not logged_in_user:
        return RedirectResponse(url="/")

    following_data = await user.get_user_follows(
        access_token=logged_in_user["access_token"], user_id=logged_in_user["id"]
    )
    return {"following": following_data}