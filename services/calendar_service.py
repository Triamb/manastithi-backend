"""
Google Calendar Service for Manastithi
Creates calendar events with Google Meet links
"""

import os
import json
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("manastithi.calendar")

# CSRF state for OAuth - simple in-memory store (fine for single-instance)
_oauth_states: set = set()
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OAuth2 Scopes needed for Calendar + Meet
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Path to store credentials
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'google_credentials.json')
TOKEN_PATH = os.path.join(os.path.dirname(__file__), '..', 'google_token.json')

# OAuth redirect URI (must match Google Cloud Console)
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/calendar/oauth/callback')


def get_client_config() -> dict:
    """Get OAuth client config from environment or file."""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        }

    # Try loading from file
    if os.path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH, 'r') as f:
            return json.load(f)

    return None


def get_stored_credentials() -> Optional[Credentials]:
    """Load stored OAuth credentials if they exist."""
    if not os.path.exists(TOKEN_PATH):
        return None

    try:
        with open(TOKEN_PATH, 'r') as f:
            token_data = json.load(f)

        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes')
        )

        # Check if credentials are valid
        if creds and creds.valid:
            return creds

        # Try to refresh if expired
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            save_credentials(creds)
            return creds

    except Exception as e:
        logger.error(f"Error loading credentials: {e}")

    return None


def save_credentials(creds: Credentials):
    """Save OAuth credentials to file."""
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    with open(TOKEN_PATH, 'w') as f:
        json.dump(token_data, f)


def is_authorized() -> bool:
    """Check if we have valid Google credentials."""
    creds = get_stored_credentials()
    return creds is not None and creds.valid


def get_authorization_url() -> Optional[str]:
    """Generate OAuth authorization URL."""
    client_config = get_client_config()
    if not client_config:
        return None

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state,
    )

    return auth_url


def validate_oauth_state(state: str) -> bool:
    """Validate and consume CSRF state token."""
    if state in _oauth_states:
        _oauth_states.discard(state)
        return True
    return False


def handle_oauth_callback(authorization_code: str) -> bool:
    """Handle OAuth callback and save credentials."""
    client_config = get_client_config()
    if not client_config:
        return False

    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        flow.fetch_token(code=authorization_code)
        creds = flow.credentials
        save_credentials(creds)
        return True

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return False


def create_meet_event(
    title: str,
    description: str,
    start_datetime: datetime,
    duration_minutes: int = 45,
    attendee_email: Optional[str] = None
) -> dict:
    """
    Create a Google Calendar event with Meet link.

    Returns:
        dict with 'success', 'meet_link', 'event_id', 'calendar_link', or 'error'
    """
    creds = get_stored_credentials()

    if not creds:
        return {
            'success': False,
            'error': 'Google Calendar not authorized. Please authorize first.',
            'needs_auth': True
        }

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Calculate end time
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        # Create event with Google Meet
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"manastithi-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                    {'method': 'popup', 'minutes': 60},       # 1 hour before
                ],
            },
        }

        # Add attendee if provided
        if attendee_email:
            event['attendees'] = [{'email': attendee_email}]

        # Create the event
        event_result = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all' if attendee_email else 'none'
        ).execute()

        # Extract Meet link
        meet_link = None
        if 'conferenceData' in event_result:
            entry_points = event_result['conferenceData'].get('entryPoints', [])
            for entry in entry_points:
                if entry.get('entryPointType') == 'video':
                    meet_link = entry.get('uri')
                    break

        return {
            'success': True,
            'meet_link': meet_link,
            'event_id': event_result.get('id'),
            'calendar_link': event_result.get('htmlLink')
        }

    except HttpError as e:
        print(f"Google Calendar API error: {e}")
        return {
            'success': False,
            'error': f'Calendar API error: {str(e)}'
        }
    except Exception as e:
        print(f"Meet creation error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def parse_appointment_datetime(date_str: str, time_slot: str) -> datetime:
    """
    Parse appointment date and time slot into datetime.

    Args:
        date_str: Date in YYYY-MM-DD format
        time_slot: Time like "10:00 AM" or "2:00 PM"

    Returns:
        datetime object
    """
    # Parse date
    date = datetime.strptime(date_str, '%Y-%m-%d')

    # Parse time slot
    time_str = time_slot.strip().upper()

    # Handle formats like "10:00 AM", "2:00 PM"
    if 'AM' in time_str or 'PM' in time_str:
        time_str = time_str.replace(' ', '')
        time_obj = datetime.strptime(time_str, '%I:%M%p')
    else:
        # 24-hour format
        time_obj = datetime.strptime(time_str, '%H:%M')

    # Combine date and time
    return datetime.combine(date.date(), time_obj.time())


def create_appointment_meet(
    user_name: str,
    user_email: str,
    service_type: str,
    appointment_date: str,
    time_slot: str
) -> dict:
    """
    Create a Meet event for an approved appointment.

    Args:
        user_name: Client's name
        user_email: Client's email
        service_type: 'consultation' or 'dmit'
        appointment_date: Date in YYYY-MM-DD format
        time_slot: Time like "10:00 AM"

    Returns:
        dict with success status and meet_link
    """
    # Determine duration based on service type
    duration = 90 if service_type == 'dmit' else 45

    # Create title
    service_name = "DMIT Assessment" if service_type == 'dmit' else "Career & Wellness Consultation"
    title = f"Manastithi: {service_name} - {user_name or 'Client'}"

    # Create description
    description = f"""Manastithi Session

Service: {service_name}
Client: {user_name or 'N/A'}
Email: {user_email}

Please join the meeting on time. If you need to reschedule, contact us at least 24 hours in advance.

Best regards,
Dr. Kshitija
Manastithi - Mental Health & Career Counseling
"""

    # Parse datetime
    try:
        start_dt = parse_appointment_datetime(appointment_date, time_slot)
    except Exception as e:
        return {
            'success': False,
            'error': f'Invalid date/time format: {e}'
        }

    # Create the Meet event
    return create_meet_event(
        title=title,
        description=description,
        start_datetime=start_dt,
        duration_minutes=duration,
        attendee_email=user_email
    )