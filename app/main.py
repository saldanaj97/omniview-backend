from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, users, public
from app.core.config import SECRET_KEY, TEMPLATES_DIR

# Create FastAPI app
app = FastAPI(
    title="OmniView Backend",
    description="OmniView Backend API",
    version="0.1.0",
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=False,  # Set to True in production with HTTPS
    same_site="lax",
)

# Set up templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/user", tags=["users"])
app.include_router(public.router, prefix="/public", tags=["public"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    access_token = request.session.get("access_token")
    return templates.TemplateResponse(
        "index.html", {"request": request, "token": access_token}
    )


# Home route that shows login or user info
@app.get("/user", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)