"""
Email Service for Manastithi
Uses Resend for sending transactional emails
"""

import os
import html
import logging
import resend
from typing import Optional
from datetime import datetime

logger = logging.getLogger("manastithi.email")

# Configure Resend
resend.api_key = os.getenv("RESEND_API_KEY", "")

# Email configuration
FROM_EMAIL = os.getenv("FROM_EMAIL", "Manastithi <noreply@manastithi.com>")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@manastithi.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ADMIN_EMAIL = os.getenv("SUPPORT_EMAIL", "triambtalwar03@gmail.com")


def esc(value) -> str:
    """Escape user-supplied values for safe HTML embedding."""
    if value is None:
        return ''
    return html.escape(str(value), quote=True)


def get_base_template(content: str, title: str = "Manastithi") -> str:
    """Wrap content in base email template with branding."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8F9FA; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F8F9FA; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">Manastithi</h1>
                            <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Your Mental Wellness Partner</p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            {content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F8F9FA; padding: 25px 30px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="margin: 0; color: #6B7280; font-size: 13px;">
                                Questions? Reply to this email or contact us at<br>
                                <a href="mailto:{SUPPORT_EMAIL}" style="color: #E37222; text-decoration: none;">{SUPPORT_EMAIL}</a>
                            </p>
                            <p style="margin: 15px 0 0 0; color: #9CA3AF; font-size: 12px;">
                                Manastithi - Mental Health & Career Counseling<br>
                                Delhi NCR, India
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Unsubscribe -->
                <p style="margin: 20px 0 0 0; color: #9CA3AF; font-size: 11px; text-align: center;">
                    This is a transactional email related to your Manastithi account.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def send_appointment_confirmation(
    to_email: str,
    user_name: str,
    service_type: str,
    appointment_date: str,
    time_slot: str,
    amount: int
) -> dict:
    """Send appointment booking confirmation email."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"
    amount_display = f"₹{amount / 100:,.0f}"

    # Parse and format date
    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
        date_display = date_obj.strftime("%A, %B %d, %Y")
    except:
        date_display = appointment_date

    content = f"""
        <h2 style="margin: 0 0 20px 0; color: #2D2D2D; font-size: 22px;">Booking Confirmed!</h2>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Thank you for booking with Manastithi! Your appointment request has been received and is pending approval.
        </p>

        <!-- Appointment Details Card -->
        <div style="background-color: #FFF7ED; border: 1px solid #FDBA74; border-radius: 12px; padding: 25px; margin: 25px 0;">
            <h3 style="margin: 0 0 15px 0; color: #C2410C; font-size: 16px; font-weight: 600;">Appointment Details</h3>

            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Service:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{service_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Date:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{date_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Time:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{time_slot}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Amount Paid:</td>
                    <td style="padding: 8px 0; color: #059669; font-size: 14px; font-weight: 600; text-align: right;">{amount_display}</td>
                </tr>
            </table>
        </div>

        <p style="margin: 25px 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            <strong>What's next?</strong><br>
            Dr. Kshitija will review your booking and confirm your appointment within 24 hours. You'll receive another email with your session link once approved.
        </p>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            We're looking forward to helping you on your wellness journey!
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            Warm regards,<br>
            <strong style="color: #E37222;">The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Booking Confirmed - Manastithi")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Booking Confirmed: {service_display} on {date_display}",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_appointment_approved(
    to_email: str,
    user_name: str,
    service_type: str,
    appointment_date: str,
    time_slot: str,
    meet_link: str
) -> dict:
    """Send appointment approval email with meeting link."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"

    # Parse and format date
    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
        date_display = date_obj.strftime("%A, %B %d, %Y")
    except:
        date_display = appointment_date

    content = f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background-color: #D1FAE5; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <span style="font-size: 32px;">&#10003;</span>
            </div>
            <h2 style="margin: 0; color: #059669; font-size: 24px;">Appointment Approved!</h2>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Great news! Your appointment has been approved by Dr. Kshitija. Here are your session details:
        </p>

        <!-- Appointment Details Card -->
        <div style="background-color: #ECFDF5; border: 1px solid #6EE7B7; border-radius: 12px; padding: 25px; margin: 25px 0;">
            <h3 style="margin: 0 0 15px 0; color: #047857; font-size: 16px; font-weight: 600;">Session Details</h3>

            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Service:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{service_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Date:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{date_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Time:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{time_slot}</td>
                </tr>
            </table>
        </div>

        <!-- Join Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{meet_link}" style="display: inline-block; background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                Join Google Meet Session
            </a>
            <p style="margin: 10px 0 0 0; color: #9CA3AF; font-size: 12px;">
                Link: {meet_link}
            </p>
        </div>

        <div style="background-color: #FEF3C7; border-radius: 8px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; color: #92400E; font-size: 14px;">
                <strong>Reminder:</strong> Please join the meeting 5 minutes early. Make sure you're in a quiet space with a stable internet connection.
            </p>
        </div>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            We're excited to meet you and support you on your wellness journey!
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            See you soon,<br>
            <strong style="color: #E37222;">Dr. Kshitija & The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Appointment Approved - Manastithi")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Your {service_display} is Confirmed for {date_display}",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_appointment_rejected(
    to_email: str,
    user_name: str,
    service_type: str,
    appointment_date: str,
    time_slot: str,
    reason: Optional[str] = None
) -> dict:
    """Send appointment rejection email."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"

    # Parse and format date
    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
        date_display = date_obj.strftime("%A, %B %d, %Y")
    except:
        date_display = appointment_date

    reason_text = esc(reason) or "the selected time slot is no longer available"

    content = f"""
        <h2 style="margin: 0 0 20px 0; color: #2D2D2D; font-size: 22px;">Appointment Update</h2>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Unfortunately, we couldn't confirm your {service_display} appointment for {date_display} at {time_slot}.
        </p>

        <div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 20px; margin: 25px 0;">
            <p style="margin: 0; color: #991B1B; font-size: 14px;">
                <strong>Reason:</strong> {reason_text}
            </p>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            <strong>Don't worry!</strong> Your payment will be refunded within 5-7 business days. Please feel free to book another slot that works better for you.
        </p>

        <!-- Rebook Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://manastithi.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                Book Another Slot
            </a>
        </div>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            We apologize for any inconvenience and look forward to seeing you soon.
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            Warm regards,<br>
            <strong style="color: #E37222;">The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Appointment Update - Manastithi")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Appointment Update: {service_display} on {date_display}",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_report_ready(
    to_email: str,
    user_name: str,
    report_title: str,
    report_type: str
) -> dict:
    """Send notification when a report is uploaded for a user."""

    type_display = {
        "dmit": "DMIT",
        "psychometric": "Psychometric",
        "career": "Career Assessment",
        "other": "Assessment"
    }.get(report_type, "Assessment")

    content = f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background-color: #EDE9FE; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <span style="font-size: 32px;">&#128196;</span>
            </div>
            <h2 style="margin: 0; color: #7C3AED; font-size: 24px;">Your Report is Ready!</h2>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Great news! Your <strong>{type_display} Report</strong> is now available in your Manastithi dashboard.
        </p>

        <!-- Report Card -->
        <div style="background-color: #F5F3FF; border: 1px solid #C4B5FD; border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center;">
            <h3 style="margin: 0 0 10px 0; color: #5B21B6; font-size: 18px; font-weight: 600;">{report_title}</h3>
            <p style="margin: 0; color: #7C3AED; font-size: 14px;">Type: {type_display} Report</p>
        </div>

        <!-- View Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://manastithi.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                View My Report
            </a>
        </div>

        <p style="margin: 0 0 15px 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            This report contains valuable insights about your assessment. Log in to your dashboard to view and download it.
        </p>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            If you have any questions about your report, feel free to reach out to us.
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            Best wishes,<br>
            <strong style="color: #E37222;">Dr. Kshitija & The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Your Report is Ready - Manastithi")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Your {type_display} Report is Ready - {report_title}",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_reminder_email(
    to_email: str,
    user_name: str,
    service_type: str,
    appointment_date: str,
    time_slot: str,
    meet_link: str,
    hours_until: int
) -> dict:
    """Send reminder email before session (24hr or 1hr)."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"

    # Parse and format date
    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
        date_display = date_obj.strftime("%A, %B %d, %Y")
    except:
        date_display = appointment_date

    if hours_until <= 1:
        time_text = "in 1 hour"
        urgency = "starting soon"
    else:
        time_text = "tomorrow"
        urgency = "coming up"

    content = f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background-color: #DBEAFE; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <span style="font-size: 32px;">&#128276;</span>
            </div>
            <h2 style="margin: 0; color: #1D4ED8; font-size: 24px;">Reminder: Session {urgency}!</h2>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Just a friendly reminder that your <strong>{service_display}</strong> session is {time_text}!
        </p>

        <!-- Session Details Card -->
        <div style="background-color: #EFF6FF; border: 1px solid #93C5FD; border-radius: 12px; padding: 25px; margin: 25px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Date:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{date_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Time:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{time_slot}</td>
                </tr>
            </table>
        </div>

        <!-- Join Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{meet_link}" style="display: inline-block; background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                Join Session
            </a>
        </div>

        <div style="background-color: #FEF3C7; border-radius: 8px; padding: 15px; margin: 25px 0;">
            <p style="margin: 0; color: #92400E; font-size: 14px;">
                <strong>Tips for your session:</strong><br>
                - Join 5 minutes early<br>
                - Find a quiet, private space<br>
                - Have your questions ready<br>
                - Keep a notebook handy
            </p>
        </div>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            We're looking forward to seeing you!
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            See you soon,<br>
            <strong style="color: #E37222;">Dr. Kshitija & The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Session Reminder - Manastithi")

    subject = f"Reminder: Your {service_display} is {time_text}!"

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_session_followup(
    to_email: str,
    user_name: str,
    service_type: str
) -> dict:
    """Send follow-up email after session completion."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"

    content = f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background-color: #D1FAE5; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <span style="font-size: 32px;">&#128079;</span>
            </div>
            <h2 style="margin: 0; color: #059669; font-size: 24px;">Thank You for Your Session!</h2>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Hi {esc(user_name) or 'there'},
        </p>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            Thank you for attending your <strong>{service_display}</strong> session with Dr. Kshitija! We hope it was valuable and insightful.
        </p>

        <div style="background-color: #ECFDF5; border: 1px solid #6EE7B7; border-radius: 12px; padding: 25px; margin: 25px 0;">
            <h3 style="margin: 0 0 15px 0; color: #047857; font-size: 16px; font-weight: 600;">What's Next?</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4B5563; font-size: 14px; line-height: 1.8;">
                <li>Your detailed report will be uploaded to your dashboard soon</li>
                <li>Review the insights and recommendations shared during the session</li>
                <li>Feel free to reach out if you have any follow-up questions</li>
            </ul>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            <strong>We'd love your feedback!</strong> Your experience helps us improve and serve you better.
        </p>

        <!-- Feedback Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://manastithi.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                Visit Your Dashboard
            </a>
        </div>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            Remember, we're here to support you on your journey. Don't hesitate to book another session whenever you need guidance.
        </p>

        <p style="margin: 30px 0 0 0; color: #4B5563; font-size: 15px;">
            With warm regards,<br>
            <strong style="color: #E37222;">Dr. Kshitija & The Manastithi Team</strong>
        </p>
    """

    html = get_base_template(content, "Thank You - Manastithi")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Thank You for Your {service_display} Session!",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}


def send_admin_new_booking(
    admin_email: str,
    user_name: str,
    user_email: str,
    service_type: str,
    appointment_date: str,
    time_slot: str,
    amount: int
) -> dict:
    """Send notification to admin when a new booking is made."""

    service_display = "Career Consultation" if service_type == "consultation" else "DMIT Assessment"
    amount_display = f"₹{amount / 100:,.0f}"

    # Parse and format date
    try:
        date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
        date_display = date_obj.strftime("%A, %B %d, %Y")
    except:
        date_display = appointment_date

    content = f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="display: inline-block; background-color: #DBEAFE; border-radius: 50%; padding: 15px; margin-bottom: 15px;">
                <span style="font-size: 32px;">&#128227;</span>
            </div>
            <h2 style="margin: 0; color: #1D4ED8; font-size: 24px;">New Booking Received!</h2>
        </div>

        <p style="margin: 0 0 25px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
            A new session booking has been made and requires your approval.
        </p>

        <!-- Booking Details Card -->
        <div style="background-color: #EFF6FF; border: 1px solid #93C5FD; border-radius: 12px; padding: 25px; margin: 25px 0;">
            <h3 style="margin: 0 0 15px 0; color: #1E40AF; font-size: 16px; font-weight: 600;">Booking Details</h3>

            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Client:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{esc(user_name) or 'Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Email:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right;">{user_email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Service:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{service_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Date:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{date_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Time:</td>
                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; font-weight: 600; text-align: right;">{time_slot}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Amount Paid:</td>
                    <td style="padding: 8px 0; color: #059669; font-size: 14px; font-weight: 600; text-align: right;">{amount_display}</td>
                </tr>
            </table>
        </div>

        <!-- Action Button -->
        <div style="text-align: center; margin: 30px 0;">
            <a href="{FRONTEND_URL}/admin" style="display: inline-block; background: linear-gradient(135deg, #E37222 0%, #C85E1A 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                Review & Approve
            </a>
        </div>

        <p style="margin: 0; color: #4B5563; font-size: 15px; line-height: 1.6;">
            Please review and approve/reject this booking in the admin dashboard. The client is waiting for confirmation.
        </p>
    """

    html = get_base_template(content, "New Booking - Manastithi Admin")

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [admin_email],
            "subject": f"New Booking: {service_display} - {esc(user_name) or esc(user_email)}",
            "html": html
        })
        return {"success": True, "id": result.get("id")}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"success": False, "error": str(e)}