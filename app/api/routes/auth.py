from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app.core.security import generate_state_token
from app.services import auth, user

router = APIRouter()

# Keep track of valid states in memory (not ideal for production with multiple servers)
# But works fine for development and single-server deployments
VALID_STATES = set()


@router.get("/")
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
    # Generate access token by following client credentials flow
    token_data = await auth.get_client_credentials_oauth_token()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in")

    if "session" in request.scope:
        request.session["access_token"] = access_token
        request.session["expires_in"] = expires_in

    return Response(content="Access token generated successfully.")


@router.get("/twitch")
async def twitch_auth():
    """
    Initiates the Twitch OAuth authentication flow.

    This function generates a random state token for CSRF protection,
    stores it in a global set of valid states, and redirects the user
    to the Twitch authorization page.

    Returns:
        RedirectResponse: A redirect to the Twitch authorization URL.
    """
    # Generate a random state string to prevent CSRF
    state = generate_state_token()

    # Store the state in our valid states set
    VALID_STATES.add(state)

    # Set a reasonable TTL by scheduling cleanup (would require background tasks)
    # For now, we'll keep it simple and just store it

    # Get authorization URL with state
    auth_url = auth.get_authorization_url(state)

    # Redirect to Twitch
    return RedirectResponse(url=auth_url)


@router.get("/twitch/callback")
async def twitch_callback(
    request: Request, code: str = None, state: str = None, error: str = None
):
    """
    Handles the callback from Twitch OAuth authentication flow.

    This function validates the state token for CSRF protection,
    exchanges the authorization code for access and refresh tokens,
    retrieves the user profile, and stores the authentication data in session.

    Args:
        request (Request): The FastAPI request object.
        code (str, optional): The authorization code from Twitch.
        state (str, optional): The state token for CSRF validation.
        error (str, optional): Error message from Twitch, if any.

    Returns:
        RedirectResponse: A redirect to the home page or error page.

    Raises:
        HTTPException: If the state is invalid or missing.
    """
    # Handle error or cancelled authentication
    if error:
        return RedirectResponse(url=f"/?error={error}")

    # Validate state if provided
    is_valid_state = state and state in VALID_STATES

    # Remove the state from valid states (one-time use)
    if state and state in VALID_STATES:
        VALID_STATES.remove(state)

    # Check if state is valid
    if not is_valid_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter. This could be a CSRF attempt or the session has expired.",
        )

    # State is missing
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    # Exchange code for token
    token_data = await auth.get_oauth_token(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # Get user profile
    user_profile = await user.get_user_profile(access_token)

    # Store tokens and profile in session
    user_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        **user_profile,
    }

    if "session" in request.scope:
        request.session["user"] = user_data

    return Response(content="Authentication successful.")


@router.get("/logout")
async def logout(request: Request):
    """
    Logout an authenticated user by clearing the session.

    This function handles user logout by removing all session data.
    After the session is cleared, the user is redirected to the home page.

    Args:
        request (Request): The FastAPI request object containing the session.

    Returns:
        RedirectResponse: A redirect response to the home page.
    """
    if "session" in request.scope:
        request.session.clear()
    return Response(content="Logged out successfully.")
