import httpx
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/top_streams")
async def top_streams(request: Request):
    """
    Endpoint to get top streams from Kick.
    """
    if not request.session.get("kick_credentials"):
        raise HTTPException(
            status_code=401,
            detail="No valid app access token found.",
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.kick.com/public/v1/livestreams",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": (
                        f"Bearer {request.session['kick_credentials'].get('access_token')}"
                    ),
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to retrieve top streams: {response.text}",
            )

        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
