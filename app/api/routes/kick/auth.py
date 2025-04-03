import base64
import json

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import (
    KICK_CLIENT_ID,
    KICK_CLIENT_SECRET,
    KICK_ENDPOINTS,
    KICK_REDIRECT_URL,
    KICK_SCOPES,
)
from app.core.security import generate_code_challenge, generate_code_verifier

router = APIRouter()


@router.get("/authenticated")
async def index(request: Request):
    """Home page with authentication link"""
    if request.session.get("kick_credentials"):
        return request.session["kick_credentials"]

    return {
        "message": "Kick OAuth2 Authentication",
        "authenticate": f"{request.url_for('kick_oauth_redirect')}",
    }


@router.get("/oauth/public_token")
async def kick_public_token(request: Request):
    """
    Endpoint to exchange authorization code for access token.
    This follows the OAuth 2.0 authorization code flow with PKCE.
    """
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": KICK_CLIENT_ID,
            "client_secret": KICK_CLIENT_SECRET,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                KICK_ENDPOINTS["tokenUrl"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get token: {response.text}",
            )

            # Save credentials to session
        credentials = response.json()
        if not credentials:
            raise HTTPException(
                status_code=400, detail="No public app access token credentials found"
            )

        # Store the credentials in the session
        if "session" in request.scope:
            request.session["kick_public_credentials"] = credentials

        # Return the token response directly
        return response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/oauth")
async def kick_oauth_redirect():
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    state_data = json.dumps({"codeVerifier": code_verifier})
    state_encoded = base64.urlsafe_b64encode(state_data.encode()).decode()

    auth_params = {
        "client_id": KICK_CLIENT_ID,
        "redirect_uri": KICK_REDIRECT_URL,
        "response_type": "code",
        "scope": " ".join(KICK_SCOPES),
        "state": state_encoded,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = f"{KICK_ENDPOINTS['authURL']}?{httpx.QueryParams(auth_params)}"
    return {"url": auth_url}


@router.get("/oauth/callback")
async def kick_oauth_callback(request: Request, code: str, state: str):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        state_decoded = json.loads(base64.urlsafe_b64decode(state).decode())
        code_verifier = state_decoded["codeVerifier"]

        token_params = {
            "grant_type": "authorization_code",
            "client_id": KICK_CLIENT_ID,
            "client_secret": KICK_CLIENT_SECRET,
            "redirect_uri": KICK_REDIRECT_URL,
            "code_verifier": code_verifier,
            "code": code,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                KICK_ENDPOINTS["tokenURL"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=token_params,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to get token"
            )

        # Save credentials to session
        credentials = response.json()
        if not credentials:
            raise HTTPException(status_code=400, detail="No credentials found")

        # Store the credentials in the session
        if "session" in request.scope:
            request.session["kick_credentials"] = credentials

        return RedirectResponse(
            url="http://localhost:3000/auth/success", status_code=302
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/oauth/refresh")
async def kick_refresh_token(request: Request):
    """
    Endpoint to refresh an access token using the stored refresh token in the session.
    """
    if not request.session.get("kick_credentials"):
        raise HTTPException(
            status_code=401,
            detail="No authenticated session found. Please authenticate first.",
        )

    credentials = request.session["kick_credentials"]
    refresh_token = credentials.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=400, detail="No refresh token found in current session"
        )

    try:
        token_params = {
            "grant_type": "refresh_token",
            "client_id": KICK_CLIENT_ID,
            "client_secret": KICK_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                KICK_ENDPOINTS["tokenURL"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=token_params,
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to refresh token: {response.text}",
            )

        # Update the stored credentials with the new tokens
        new_credentials = response.json()
        request.session["kick_credentials"] = new_credentials

        return new_credentials

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Add a clear endpoint for consistency
@router.get("/clear")
async def clear_credentials(request: Request):
    """Clear credentials from session"""
    if "session" in request.scope and "kick_credentials" in request.session:
        request.session.pop("kick_credentials", None)
    return {"message": "Kick credentials have been cleared"}
