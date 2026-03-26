"""
Email Router for Manastithi API
Handles email sending endpoints - requires authentication
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from services.email_service import (
    send_appointment_confirmation,
    send_appointment_approved,
    send_appointment_rejected,
    send_report_ready,
    send_reminder_email,
    send_session_followup,
    send_admin_new_booking
)
from services.auth import require_auth, require_admin
from services.rate_limit import email_rate_limit

logger = logging.getLogger("manastithi.email")

# Server-side admin email - NEVER accept from client
ADMIN_EMAIL = os.getenv("SUPPORT_EMAIL", "triambtalwar03@gmail.com")

router = APIRouter(prefix="/email", tags=["email"], dependencies=[Depends(email_rate_limit)])


class AppointmentConfirmationRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    service_type: str = Field(..., max_length=50)
    appointment_date: str = Field(..., max_length=20)
    time_slot: str = Field(..., max_length=20)
    amount: int = Field(..., ge=0, le=10000000)


class AppointmentApprovedRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    service_type: str = Field(..., max_length=50)
    appointment_date: str = Field(..., max_length=20)
    time_slot: str = Field(..., max_length=20)
    meet_link: str = Field(..., max_length=500)


class AppointmentRejectedRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    service_type: str = Field(..., max_length=50)
    appointment_date: str = Field(..., max_length=20)
    time_slot: str = Field(..., max_length=20)
    reason: Optional[str] = Field(None, max_length=500)


class ReportReadyRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    report_title: str = Field(..., max_length=200)
    report_type: str = Field(..., max_length=50)


class ReminderRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    service_type: str = Field(..., max_length=50)
    appointment_date: str = Field(..., max_length=20)
    time_slot: str = Field(..., max_length=20)
    meet_link: str = Field(..., max_length=500)
    hours_until: int = Field(..., ge=0, le=48)


class FollowupRequest(BaseModel):
    to_email: EmailStr
    user_name: Optional[str] = Field(None, max_length=100)
    service_type: str = Field(..., max_length=50)


class AdminNewBookingRequest(BaseModel):
    user_name: Optional[str] = None
    user_email: EmailStr
    service_type: str = Field(..., max_length=50)
    appointment_date: str = Field(..., max_length=20)
    time_slot: str = Field(..., max_length=20)
    amount: int


@router.post("/appointment-confirmation")
async def send_confirmation(
    request: AppointmentConfirmationRequest,
    current_user: dict = Depends(require_auth),
):
    """Send appointment booking confirmation email. Requires authentication."""
    # SECURITY: Users can only send confirmation emails to themselves
    if current_user["email"].lower() != request.to_email.lower():
        raise HTTPException(status_code=403, detail="Can only send confirmation to your own email")

    result = send_appointment_confirmation(
        to_email=request.to_email,
        user_name=request.user_name,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot,
        amount=request.amount
    )

    if not result.get("success"):
        logger.error(f"Failed to send confirmation email: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Confirmation email sent", "id": result.get("id")}


@router.post("/appointment-approved")
async def send_approved(
    request: AppointmentApprovedRequest,
    current_user: dict = Depends(require_admin),
):
    """Send appointment approval email with meeting link. Admin only."""
    result = send_appointment_approved(
        to_email=request.to_email,
        user_name=request.user_name,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot,
        meet_link=request.meet_link
    )

    if not result.get("success"):
        logger.error(f"Failed to send approval email: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Approval email sent", "id": result.get("id")}


@router.post("/appointment-rejected")
async def send_rejected(
    request: AppointmentRejectedRequest,
    current_user: dict = Depends(require_admin),
):
    """Send appointment rejection email. Admin only."""
    result = send_appointment_rejected(
        to_email=request.to_email,
        user_name=request.user_name,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot,
        reason=request.reason
    )

    if not result.get("success"):
        logger.error(f"Failed to send rejection email: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Rejection email sent", "id": result.get("id")}


@router.post("/report-ready")
async def send_report_notification(
    request: ReportReadyRequest,
    current_user: dict = Depends(require_admin),
):
    """Send notification when a report is ready. Admin only."""
    result = send_report_ready(
        to_email=request.to_email,
        user_name=request.user_name,
        report_title=request.report_title,
        report_type=request.report_type
    )

    if not result.get("success"):
        logger.error(f"Failed to send report notification: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Report notification email sent", "id": result.get("id")}


@router.post("/reminder")
async def send_session_reminder(
    request: ReminderRequest,
    current_user: dict = Depends(require_admin),
):
    """Send session reminder email (24hr or 1hr before). Admin only."""
    result = send_reminder_email(
        to_email=request.to_email,
        user_name=request.user_name,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot,
        meet_link=request.meet_link,
        hours_until=request.hours_until
    )

    if not result.get("success"):
        logger.error(f"Failed to send reminder email: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Reminder email sent", "id": result.get("id")}


@router.post("/session-followup")
async def send_followup(
    request: FollowupRequest,
    current_user: dict = Depends(require_admin),
):
    """Send follow-up email after session completion. Admin only."""
    result = send_session_followup(
        to_email=request.to_email,
        user_name=request.user_name,
        service_type=request.service_type
    )

    if not result.get("success"):
        logger.error(f"Failed to send follow-up email: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Follow-up email sent", "id": result.get("id")}


@router.post("/admin-new-booking")
async def send_admin_booking_notification(
    request: AdminNewBookingRequest,
    current_user: dict = Depends(require_auth),
):
    """Send notification to admin when a new booking is made. Requires authentication."""
    result = send_admin_new_booking(
        admin_email=ADMIN_EMAIL,  # SECURITY: Always use server-side admin email
        user_name=request.user_name,
        user_email=request.user_email,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        time_slot=request.time_slot,
        amount=request.amount
    )

    if not result.get("success"):
        logger.error(f"Failed to send admin booking notification: {result.get('error')}")
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": "Admin notification email sent", "id": result.get("id")}
