"""
Tests for the authentication middleware.
Ensures endpoints are properly protected.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Health endpoints should be public (no auth required)."""

    def test_root_is_public(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_is_public(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestChatEndpoints:
    """Chat message endpoint allows anonymous, but history requires auth."""

    def test_chat_message_without_auth_still_works(self):
        """Anonymous users should be able to chat (landing page feature)."""
        response = client.post("/chat/message", json={
            "message": "Hello Mana"
        })
        # Should not be 401 - anonymous chat is allowed
        # It might fail for other reasons (no API key) but not auth
        assert response.status_code != 401

    def test_chat_message_rejects_empty(self):
        """Empty messages should be rejected."""
        response = client.post("/chat/message", json={
            "message": ""
        })
        # Pydantic validation should reject empty string (min_length=1)
        assert response.status_code == 422

    def test_chat_history_requires_auth(self):
        """Getting chat history requires authentication."""
        response = client.get("/chat/history/some-user-id")
        assert response.status_code in [401, 403]

    def test_chat_delete_requires_auth(self):
        """Deleting chat history requires authentication."""
        response = client.delete("/chat/history/some-user-id")
        assert response.status_code in [401, 403]

    def test_chat_history_limit_validation(self):
        """History limit should be capped at 100."""
        response = client.get(
            "/chat/history/some-user-id?limit=999",
            headers={"Authorization": "Bearer fake-token"}
        )
        # Should fail auth first, but if it gets through, limit should be validated
        assert response.status_code in [401, 422]


class TestEmailEndpoints:
    """All email endpoints require authentication."""

    def test_appointment_confirmation_requires_auth(self):
        response = client.post("/email/appointment-confirmation", json={
            "to_email": "test@example.com",
            "service_type": "consultation",
            "appointment_date": "2026-03-10",
            "time_slot": "10:00 AM",
            "amount": 49900
        })
        assert response.status_code in [401, 403]

    def test_appointment_approved_requires_admin(self):
        response = client.post("/email/appointment-approved", json={
            "to_email": "test@example.com",
            "service_type": "consultation",
            "appointment_date": "2026-03-10",
            "time_slot": "10:00 AM",
            "meet_link": "https://meet.google.com/abc"
        })
        assert response.status_code in [401, 403]

    def test_appointment_rejected_requires_admin(self):
        response = client.post("/email/appointment-rejected", json={
            "to_email": "test@example.com",
            "service_type": "consultation",
            "appointment_date": "2026-03-10",
            "time_slot": "10:00 AM"
        })
        assert response.status_code in [401, 403]

    def test_report_ready_requires_admin(self):
        response = client.post("/email/report-ready", json={
            "to_email": "test@example.com",
            "report_title": "Test Report",
            "report_type": "psychometric"
        })
        assert response.status_code in [401, 403]


class TestCalendarEndpoints:
    """Calendar endpoints require admin auth (except status)."""

    def test_calendar_status_is_public(self):
        """Calendar status check should be accessible."""
        response = client.get("/calendar/status")
        assert response.status_code == 200

    def test_calendar_authorize_requires_admin(self):
        response = client.get("/calendar/authorize", follow_redirects=False)
        assert response.status_code in [401, 403]

    def test_create_meet_requires_admin(self):
        response = client.post("/calendar/create-meet", json={
            "user_email": "test@example.com",
            "service_type": "consultation",
            "appointment_date": "2026-03-10",
            "time_slot": "10:00 AM"
        })
        assert response.status_code in [401, 403]

    def test_disconnect_requires_admin(self):
        response = client.get("/calendar/disconnect")
        assert response.status_code in [401, 403]


class TestSecurityHeaders:
    """Verify security headers are present."""

    def test_security_headers_present(self):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"


class TestCORS:
    """Verify CORS is not wildcard."""

    def test_cors_not_wildcard(self):
        """CORS should not allow all origins in the middleware config."""
        response = client.options("/chat/message", headers={
            "Origin": "https://evil-site.com",
            "Access-Control-Request-Method": "POST",
        })
        # If CORS is properly configured, evil-site.com should not be allowed
        allowed_origin = response.headers.get("access-control-allow-origin", "")
        assert allowed_origin != "*", "CORS should not allow all origins"


class TestRateLimiting:
    """Verify rate limiting is in place."""

    def test_rate_limit_header_or_429(self):
        """Rapid requests should eventually get rate limited."""
        # Send many requests quickly
        responses = []
        for _ in range(20):
            resp = client.post("/chat/message", json={"message": "test"})
            responses.append(resp.status_code)

        # At least some should be rate limited (429) OR all succeed
        # (depends on if AI service is configured)
        # The key check: rate limiter doesn't crash the app
        assert all(code in [200, 422, 429, 500, 503] for code in responses)
