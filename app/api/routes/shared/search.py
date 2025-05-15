from fastapi import APIRouter, Query, Request

from app.services.shared.search import search_all_platforms

router = APIRouter()


@router.get("/search")
async def search_users(request: Request, q: str = Query(..., min_length=2)):
    return await search_all_platforms(request, q)
