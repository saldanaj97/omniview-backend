from fastapi import APIRouter, Depends, Header, HTTPException, Request

import app.services.twitch.public as public

router = APIRouter()


def get_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No access token found")

    token_parts = authorization.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format"
        )

    return token_parts[1]


@router.get("/status")
async def public_check_login_status(request: Request):
    """
    Public endpoint to check which platforms have access tokens available.
    This is used for public access without requiring a session.
    """
    try:
        platform_status = await public.check_public_login_status(request=request)
        return platform_status
    except Exception as e:
        return {"data": [], "error": {"message": str(e)}}


@router.get("/top-streams")
async def get_popular_streams(token: str = Depends(get_token)):
    popular_streams = await public.get_top_streams(access_token=token)
    return popular_streams["data"]
