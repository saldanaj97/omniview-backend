from fastapi import APIRouter, Request

import app.services.public as public

router = APIRouter()


@router.get("/top-streams")
async def get_popular_streams(request: Request):
    access_token = request.session["access_token"]
    popular_streams = await public.get_top_streams(access_token=access_token)
    return {"popular_streams": popular_streams}