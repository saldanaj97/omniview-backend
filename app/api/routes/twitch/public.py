from fastapi import APIRouter, Depends, Header, HTTPException

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


@router.get("/top-streams")
async def get_popular_streams(token: str = Depends(get_token)):
    popular_streams = await public.get_top_streams(access_token=token)
    return popular_streams["data"]
