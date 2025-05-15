from fastapi import APIRouter, Query, Request

from app.services.shared.search import search_all_platforms

router = APIRouter()


@router.get("/search")
async def search_users(request: Request, q: str = Query(..., min_length=2)):
    """
    Search users across all platforms by username. Uses Redis cache for repeated queries.
    """
    return await search_all_platforms(request, q)
