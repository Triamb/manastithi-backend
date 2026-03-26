"""
Authentication middleware for Manastithi API.
Verifies Supabase JWT tokens from the frontend.
"""

import os
import httpx
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Admin email whitelist - must match frontend config/admin.ts
ADMIN_EMAILS = [
    "triambtalwar03@gmail.com",
    "kshitijatalwar09@gmail.com",
]

security = HTTPBearer(auto_error=False)


async def verify_supabase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Verify a Supabase JWT token and return the user info.
    Returns None if no token provided (for endpoints that allow anonymous access).
    Raises 401 if token is invalid.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    supabase_url = os.getenv("SUPABASE_URL", "")

    if not supabase_url:
        raise HTTPException(status_code=500, detail="Auth service not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": os.getenv("SUPABASE_SERVICE_KEY", ""),
                },
            )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_data = response.json()
        return {
            "id": user_data.get("id"),
            "email": user_data.get("email"),
            "role": user_data.get("role", "authenticated"),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")


async def require_auth(
    user: Optional[dict] = Depends(verify_supabase_token),
) -> dict:
    """Require authentication - raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_admin(
    user: dict = Depends(require_auth),
) -> dict:
    """Require admin role - raises 403 if not admin."""
    if user.get("email", "").lower() not in [e.lower() for e in ADMIN_EMAILS]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_optional_user(request: Request) -> Optional[dict]:
    """Extract user from request state if available (set by middleware)."""
    return getattr(request.state, "user", None)
