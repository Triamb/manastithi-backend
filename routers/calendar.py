"""
Calendar Router for Manastithi API
Handles Google Calendar OAuth and Meet link creation
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.calendar_service import (
    is_authorized,
    get_authorization_url,
    handle_oauth_callback,
    create_appointment_meet,
    validate_oauth_state,
)
from services.auth import require_admin
from services.rate_limit import calendar_rate_limit

logger = logging.getLogger("manastithi.calendar")

router = APIRouter(prefix="/calendar", tags=["calendar"], dependencies=[Depends(calendar_rate_limit)])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class CreateMeetRequest(BaseModel):
    user_name: Optional[str] = None
    user_email: EmailStr
    service_type: str
    appointment_date: str
    time_slot: str


@router.get("/status")
async def get_calendar_status():
    """Check if Google Calendar is authorized."""
    authorized = is_authorized()
    return {
        "authorized": authorized,
        "message": "Google Calendar is connected" if authorized else "Google Calendar not connected. Please authorize."
    }


@router.get("/authorize")
async def authorize_calendar(
    _admin: dict = Depends(require_admin),
):
    """Get Google OAuth URL. Admin only. Frontend handles the redirect."""
    auth_url = get_authorization_url()

    if not auth_url:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )

    return {"auth_url": auth_url}


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    error: str = Query(None),
    state: str = Query(None),
):
    """Handle OAuth callback from Google."""

    # SECURITY: Validate CSRF state token
    if state and not validate_oauth_state(state):
        logger.warning("OAuth callback with invalid state token")
        return HTMLResponse(content=f"""
            <html><body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #dc2626;">Security Error</h1>
                <p>Invalid state parameter. Please try again.</p>
                <p><a href="{FRONTEND_URL}/admin">Return to Admin Dashboard</a></p>
            </body></html>
        """, status_code=403)

    if error:
        logger.error(f"Google OAuth error: {error}")
        return HTMLResponse(content=f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #dc2626;">Authorization Failed</h1>
                <p>Could not connect Google Calendar. Please try again.</p>
                <p><a href="{FRONTEND_URL}/admin">Return to Admin Dashboard</a></p>
            </body>
            </html>
        """)

    success = handle_oauth_callback(code)

    if success:
        return HTMLResponse(content=f"""
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <div style="max-width: 400px; margin: 0 auto; background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px; padding: 30px;">
                    <h1 style="color: #16a34a; margin-bottom: 10px;">&#10003; Connected!</h1>
                    <p style="color: #166534;">Google Calendar is now connected to Manastithi.</p>
                    <p style="color: #6b7280; font-size: 14px;">You can now approve appointments and real Google Meet links will be generated automatically.</p>
                    <a href="{FRONTEND_URL}/admin" style="display: inline-block; margin-top: 20px; background: linear-gradient(135deg, #E37222, #C85E1A); color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                        Return to Admin Dashboard
                    </a>
                </div>
            </body>
            </html>
        """)
    else:
        return HTMLResponse(content=f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #dc2626;">Authorization Failed</h1>
                <p>Could not complete OAuth flow. Please try again.</p>
                <p><a href="{FRONTEND_URL}/admin">Return to Admin Dashboard</a></p>
            </body>
            </html>
        """)


@router.post("/create-meet")
async def create_meet(
    request: CreateMeetRequest,
    _admin: dict = Depends(require_admin),
):
    """Create a Google Meet link for an appointment. Admin only."""

    result = create_appointment_meet(
        user_name=request.user_name,
        user_email=request.user_email,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot
    )

    if not result['success']:
        if result.get('needs_auth'):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Calendar authorization required",
                    "auth_url": "/calendar/authorize"
                }
            )
        logger.error(f"Failed to create meet: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to create meeting")

    return {
        "success": True,
        "meet_link": result['meet_link'],
        "event_id": result.get('event_id'),
        "calendar_link": result.get('calendar_link')
    }


@router.get("/disconnect")
async def disconnect_calendar(
    _admin: dict = Depends(require_admin),
):
    """Disconnect Google Calendar (delete stored credentials). Admin only."""
    token_path = os.path.join(os.path.dirname(__file__), '..', 'google_token.json')

    if os.path.exists(token_path):
        os.remove(token_path)
        logger.info("Google Calendar disconnected")
        return {"success": True, "message": "Google Calendar disconnected"}

    return {"success": True, "message": "No calendar was connected"}
