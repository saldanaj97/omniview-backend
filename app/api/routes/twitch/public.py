from fastapi import APIRouter, HTTPException, Request

import app.services.twitch.public as public

router = APIRouter()


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
async def get_popular_streams(request: Request):
    try:
        popular_streams = await public.get_top_streams(request=request)
        return popular_streams
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
