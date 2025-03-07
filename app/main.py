from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, public, users
from app.core.config import SECRET_KEY

# Create FastAPI app
app = FastAPI(
    title="OmniView Backend",
    description="OmniView Backend API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (CHANGE IN PRODUCTION)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=False,  # Set to True in production with HTTPS
    same_site="lax",
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/user", tags=["users"])
app.include_router(public.router, prefix="/api/public", tags=["public"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
