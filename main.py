import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging instead of print statements
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("manastithi")

# Import routers
from routers import chat, email, calendar


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Manastithi API starting up...")
    logger.info(f"  AI: OpenRouter ({os.getenv('OPENROUTER_MODEL', 'not configured')})")
    logger.info(f"  API Key: {'set' if os.getenv('OPENROUTER_API_KEY') else 'MISSING'}")

    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_configured = supabase_key and not supabase_key.startswith("your-")
    logger.info(f"  Supabase: {'connected' if supabase_configured else 'skipped (optional)'}")

    resend_key = os.getenv("RESEND_API_KEY", "")
    logger.info(f"  Email: {'Resend configured' if resend_key else 'not configured'}")

    google_client = os.getenv("GOOGLE_CLIENT_ID", "")
    logger.info(f"  Calendar: {'Google OAuth configured' if google_client else 'not configured'}")
    yield
    # Shutdown
    logger.info("Manastithi API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Manastithi API",
    description="Backend API for Manastithi - Mental Health & Career Counseling Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - use environment-based origins
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    allowed_origins = [FRONTEND_URL]
else:
    # In development, allow localhost variants
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        FRONTEND_URL,
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "apikey", "x-client-info"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Include routers
app.include_router(chat.router)
app.include_router(email.router)
app.include_router(calendar.router)


# Health check endpoint
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Manastithi API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    # SECURITY: Don't leak config details in production
    if ENVIRONMENT == "production":
        return {"status": "ok"}

    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {
        "status": "ok",
        "environment": ENVIRONMENT,
        "ai_provider": "openrouter",
        "api_key_set": bool(os.getenv("OPENROUTER_API_KEY")),
        "supabase_configured": bool(supabase_key and not supabase_key.startswith("your-")),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    is_dev = ENVIRONMENT != "production"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=is_dev,
    )
