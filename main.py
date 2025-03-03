import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import auth
import config

# Create FastAPI app
app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

# Set up templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


# Home route that shows login or user info
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


# Route to start OAuth flow
@app.get("/auth/twitch")
async def twitch_auth():
    # Generate a random state string to prevent CSRF
    state = secrets.token_hex(16)
    auth_url = auth.get_authorization_url(state)
    response = RedirectResponse(url=auth_url)
    response.set_cookie(key="oauth_state", value=state)
    return response


# OAuth callback route
@app.get("/auth/twitch/callback")
async def twitch_callback(
    request: Request, code: str = None, state: str = None, error: str = None
):
    # Handle error or cancelled authentication
    if error:
        return {"error": error}

    # Validate state to prevent CSRF
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="State verification failed")

    # Exchange code for token
    token_data = await auth.get_oauth_token(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # Get user profile
    user_profile = await auth.get_user_profile(access_token)

    # Store tokens and profile in session
    user_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        **user_profile,
    }

    request.session["user"] = user_data

    # Redirect to home page
    return RedirectResponse(url="/")


# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)
