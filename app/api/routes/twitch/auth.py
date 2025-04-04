from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.core.security import generate_state_token
from app.services.twitch import auth, user

router = APIRouter()

# Keep track of valid states in memory (not ideal for production with multiple servers)
# But works fine for development and single-server deployments
VALID_STATES = set()


@router.get("/authenticated")
async def index(request: Request):
    """
    Initiates the Twitch OAuth client credentials flow.

    This function generates an access token so users do not have
    to login to access content that does not require a login.

    Returns:
        RedirectResponse: A redirect to the home page or error page.

    Raises:
        HTTPException: If the state is invalid or missing.
    """
    if request.session.get("twitch_credentials"):
        # Check if the token is still valid, refresh if needed
        if await auth.ensure_valid_token(request):
            credentials = request.session["twitch_credentials"]
            return {
                "access_token": credentials.get("access_token"),
                "expires_in": credentials.get("expires_in"),
            }

    # Generate access token by following client credentials flow
    token_data = await auth.get_client_credentials_oauth_token()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")

    # Store in session for future use
    request.session["twitch_credentials"] = token_data

    return {"access_token": access_token, "expires_in": expires_in}


@router.get("/oauth/public_token")
async def app_access_token(request: Request):
    """
    Endpoint to exchange authorization code for access token.
    This follows the OAuth 2.0 authorization code flow.

    Returns:
        dict: Contains the access token and expiration time.

    Raises:
        HTTPException: If there is an error in obtaining the token.
    """
    if request.session.get("twitch_public_credentials"):
        # Ensure the token is valid
        if await auth.ensure_valid_token(request):
            credentials = request.session["twitch_public_credentials"]
            request.session["twitch_public_credentials"] = credentials
            return {
                "access_token": credentials.get("access_token"),
                "expires_in": credentials.get("expires_in"),
                "token_type": credentials.get("token_type", "Bearer"),
            }

    # Fallback to client credentials flow if no session data found
    token_data = await auth.get_app_access_token()
    if "session" in request.scope:
        request.session["twitch_public_credentials"] = token_data

    return {
        "access_token": token_data.get("access_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type", "Bearer"),
    }


@router.get("/login")
async def twitch_auth():
    """
    Initiates the Twitch OAuth authentication flow.
    """
    # Generate a random state string to prevent CSRF
    state = generate_state_token()

    # Store the state in our valid states set
    VALID_STATES.add(state)

    # Get authorization URL with state
    auth_url = auth.get_authorization_url(state)

    # Return the URL instead of redirecting
    return {"url": auth_url}


@router.get("/callback")
async def twitch_callback(
    request: Request, code: str = None, state: str = None, error: str = None
):
    """
    Handles the callback from Twitch OAuth authentication flow.
    """
    # Handle error or cancelled authentication
    if error:
        return RedirectResponse(url=f"http://localhost:3000?error={error}")

    # Validate state
    if not state:
        return RedirectResponse(url="http://localhost:3000?error=missing_state")

    is_valid_state = state in VALID_STATES

    # Remove the state from valid states (one-time use)
    if state in VALID_STATES:
        VALID_STATES.remove(state)

    if not is_valid_state:
        return RedirectResponse(url="http://localhost:3000?error=invalid_state")

    try:
        # Exchange code for token
        token_data = await auth.get_oauth_token(code)

        # Get user profile
        access_token = token_data.get("access_token")
        user_profile = await user.get_user_profile(access_token)
        if not user_profile:
            return RedirectResponse(
                url="http://localhost:3000?error=invalid_access_token"
            )

        if "session" in request.scope:
            request.session["twitch_user_profile"] = user_profile
            request.session["twitch_credentials"] = token_data

        return RedirectResponse(
            url="http://localhost:3000/auth/success", status_code=302
        )

    except Exception as e:
        return RedirectResponse(url=f"http://localhost:3000?error={str(e)}")


@router.get("/logout")
async def logout(request: Request):
    """
    Logout an authenticated user by clearing cookies.
    """
    response = Response(content="Logged out successfully.")

    # Only clear twitch-related session data
    if "session" in request.scope and "twitch_credentials" in request.session:
        request.session.pop("twitch_credentials", None)

    return response
