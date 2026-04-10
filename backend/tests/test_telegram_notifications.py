"""
Test suite for Master Telegram Notification Settings
Tests the new Telegram bot configuration endpoints:
- PATCH /api/masters/{master_id}/telegram - Save telegram config
- POST /api/masters/{master_id}/test-telegram - Send test message
- POST /api/masters/{master_id}/reset-notifications - Reset unread counter
- GET /api/masters/{master_id} - Returns telegram fields
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
MASTER_EMAIL = "olena@example.com"
MASTER_PASSWORD = "test123"
MASTER_ID = "726a7346-f0d5-4f1d-99cc-4b7e1f5795cc"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Another master for access control tests
OTHER_MASTER_ID = "197c3a5e-9fe0-4863-90ee-77aa0babd2c8"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def master_token(api_client):
    """Get master authentication token"""
    response = api_client.post(f"{BASE_URL}/api/masters/login", json={
        "email": MASTER_EMAIL,
        "password": MASTER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Master authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/admin/login", json={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def authenticated_master_client(api_client, master_token):
    """Session with master auth header"""
    api_client.headers.update({"Authorization": f"Bearer {master_token}"})
    return api_client


@pytest.fixture
def authenticated_admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


class TestMasterLogin:
    """Test master login functionality"""
    
    def test_master_login_success(self, api_client):
        """Test master can login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/masters/login", json={
            "email": MASTER_EMAIL,
            "password": MASTER_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "master" in data, "Response should contain master data"
        assert data["master"]["email"] == MASTER_EMAIL
        assert data["master"]["id"] == MASTER_ID
        print(f"✓ Master login successful for {MASTER_EMAIL}")
    
    def test_master_login_invalid_credentials(self, api_client):
        """Test master login fails with invalid credentials"""
        response = api_client.post(f"{BASE_URL}/api/masters/login", json={
            "email": MASTER_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Master login correctly rejected invalid credentials")


class TestGetMasterWithTelegramFields:
    """Test GET /api/masters/{master_id} returns telegram fields"""
    
    def test_get_master_returns_telegram_fields(self, authenticated_master_client):
        """Verify master profile includes telegram configuration fields"""
        response = authenticated_master_client.get(f"{BASE_URL}/api/masters/{MASTER_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify telegram fields exist in response
        assert "telegram_bot_token" in data, "Response should include telegram_bot_token"
        assert "telegram_chat_id" in data, "Response should include telegram_chat_id"
        assert "telegram_notifications_enabled" in data, "Response should include telegram_notifications_enabled"
        assert "unread_bookings_count" in data, "Response should include unread_bookings_count"
        
        # Verify types
        assert isinstance(data["telegram_notifications_enabled"], bool), "telegram_notifications_enabled should be boolean"
        assert isinstance(data["unread_bookings_count"], int), "unread_bookings_count should be integer"
        
        print(f"✓ GET /api/masters/{MASTER_ID} returns all telegram fields")
        print(f"  - telegram_bot_token: {'set' if data['telegram_bot_token'] else 'not set'}")
        print(f"  - telegram_chat_id: {'set' if data['telegram_chat_id'] else 'not set'}")
        print(f"  - telegram_notifications_enabled: {data['telegram_notifications_enabled']}")
        print(f"  - unread_bookings_count: {data['unread_bookings_count']}")


class TestPatchMasterTelegram:
    """Test PATCH /api/masters/{master_id}/telegram endpoint"""
    
    def test_save_telegram_config(self, authenticated_master_client):
        """Test saving telegram bot configuration"""
        config = {
            "telegram_bot_token": "test_token_123456:ABC",
            "telegram_chat_id": "123456789",
            "telegram_notifications_enabled": True
        }
        
        response = authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json=config
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data["notifications_enabled"] == True, "notifications_enabled should be True"
        
        print("✓ PATCH /api/masters/{master_id}/telegram - Config saved successfully")
    
    def test_verify_telegram_config_persisted(self, authenticated_master_client):
        """Verify telegram config was actually saved by fetching master profile"""
        response = authenticated_master_client.get(f"{BASE_URL}/api/masters/{MASTER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["telegram_bot_token"] == "test_token_123456:ABC", "Bot token should be persisted"
        assert data["telegram_chat_id"] == "123456789", "Chat ID should be persisted"
        assert data["telegram_notifications_enabled"] == True, "Notifications enabled should be persisted"
        
        print("✓ Telegram config verified as persisted in database")
    
    def test_disable_telegram_notifications(self, authenticated_master_client):
        """Test disabling telegram notifications"""
        config = {
            "telegram_bot_token": "test_token_123456:ABC",
            "telegram_chat_id": "123456789",
            "telegram_notifications_enabled": False
        }
        
        response = authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json=config
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["notifications_enabled"] == False
        
        print("✓ Telegram notifications disabled successfully")
    
    def test_clear_telegram_config(self, authenticated_master_client):
        """Test clearing telegram configuration"""
        config = {
            "telegram_bot_token": None,
            "telegram_chat_id": None,
            "telegram_notifications_enabled": False
        }
        
        response = authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json=config
        )
        assert response.status_code == 200
        
        # Verify cleared
        get_response = authenticated_master_client.get(f"{BASE_URL}/api/masters/{MASTER_ID}")
        data = get_response.json()
        assert data["telegram_bot_token"] is None, "Bot token should be cleared"
        assert data["telegram_chat_id"] is None, "Chat ID should be cleared"
        
        print("✓ Telegram config cleared successfully")


class TestTelegramAccessControl:
    """Test access control for telegram endpoints"""
    
    def test_master_cannot_modify_other_master_telegram(self, authenticated_master_client):
        """Test that a master cannot modify another master's telegram settings"""
        config = {
            "telegram_bot_token": "hacker_token",
            "telegram_chat_id": "hacker_chat",
            "telegram_notifications_enabled": True
        }
        
        response = authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{OTHER_MASTER_ID}/telegram",
            json=config
        )
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"
        
        print("✓ Access control: Master cannot modify another master's telegram settings")
    
    def test_master_cannot_test_other_master_telegram(self, authenticated_master_client):
        """Test that a master cannot send test message for another master"""
        response = authenticated_master_client.post(
            f"{BASE_URL}/api/masters/{OTHER_MASTER_ID}/test-telegram"
        )
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"
        
        print("✓ Access control: Master cannot test another master's telegram")
    
    def test_master_cannot_reset_other_master_notifications(self, authenticated_master_client):
        """Test that a master cannot reset another master's notification counter"""
        response = authenticated_master_client.post(
            f"{BASE_URL}/api/masters/{OTHER_MASTER_ID}/reset-notifications"
        )
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"
        
        print("✓ Access control: Master cannot reset another master's notifications")
    
    def test_unauthenticated_cannot_access_telegram_endpoints(self, api_client):
        """Test that unauthenticated requests are rejected"""
        # Remove auth header
        api_client.headers.pop("Authorization", None)
        
        response = api_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json={"telegram_notifications_enabled": True}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print("✓ Access control: Unauthenticated requests rejected")


class TestTestTelegramEndpoint:
    """Test POST /api/masters/{master_id}/test-telegram endpoint"""
    
    def test_test_telegram_without_config(self, authenticated_master_client):
        """Test sending test message when telegram is not configured"""
        # First clear the config
        authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json={
                "telegram_bot_token": None,
                "telegram_chat_id": None,
                "telegram_notifications_enabled": False
            }
        )
        
        response = authenticated_master_client.post(
            f"{BASE_URL}/api/masters/{MASTER_ID}/test-telegram"
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        
        print("✓ Test telegram correctly fails when not configured")
    
    def test_test_telegram_with_invalid_token(self, authenticated_master_client):
        """Test sending test message with invalid bot token (should fail gracefully)"""
        # Set up invalid config
        authenticated_master_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json={
                "telegram_bot_token": "invalid_token_12345",
                "telegram_chat_id": "123456789",
                "telegram_notifications_enabled": True
            }
        )
        
        response = authenticated_master_client.post(
            f"{BASE_URL}/api/masters/{MASTER_ID}/test-telegram"
        )
        
        # Should return 400 with Telegram API error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        assert "Telegram" in data["detail"] or "помилка" in data["detail"].lower(), \
            f"Error should mention Telegram API issue: {data['detail']}"
        
        print(f"✓ Test telegram fails gracefully with invalid token: {data['detail']}")


class TestResetNotificationsEndpoint:
    """Test POST /api/masters/{master_id}/reset-notifications endpoint"""
    
    def test_reset_notifications_counter(self, authenticated_master_client):
        """Test resetting the unread bookings counter"""
        response = authenticated_master_client.post(
            f"{BASE_URL}/api/masters/{MASTER_ID}/reset-notifications"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data["unread_bookings_count"] == 0, "Counter should be reset to 0"
        
        print("✓ Reset notifications counter successful")
    
    def test_verify_counter_reset_persisted(self, authenticated_master_client):
        """Verify the counter reset was persisted"""
        response = authenticated_master_client.get(f"{BASE_URL}/api/masters/{MASTER_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["unread_bookings_count"] == 0, "Counter should remain 0 after reset"
        
        print("✓ Counter reset verified as persisted")
    
    def test_reset_nonexistent_master(self, authenticated_admin_client):
        """Test resetting notifications for non-existent master"""
        response = authenticated_admin_client.post(
            f"{BASE_URL}/api/masters/nonexistent-id-12345/reset-notifications"
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✓ Reset notifications returns 404 for non-existent master")


class TestAdminAccessToTelegramEndpoints:
    """Test that admin can access telegram endpoints for any master"""
    
    def test_admin_can_view_master_telegram_settings(self, authenticated_admin_client):
        """Test admin can view any master's telegram settings"""
        response = authenticated_admin_client.get(f"{BASE_URL}/api/masters/{MASTER_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "telegram_bot_token" in data
        assert "telegram_chat_id" in data
        assert "telegram_notifications_enabled" in data
        
        print("✓ Admin can view master's telegram settings")
    
    def test_admin_can_modify_master_telegram_settings(self, authenticated_admin_client):
        """Test admin can modify any master's telegram settings"""
        config = {
            "telegram_bot_token": "admin_set_token",
            "telegram_chat_id": "admin_set_chat",
            "telegram_notifications_enabled": False
        }
        
        response = authenticated_admin_client.patch(
            f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
            json=config
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Admin can modify master's telegram settings")
    
    def test_admin_can_reset_master_notifications(self, authenticated_admin_client):
        """Test admin can reset any master's notification counter"""
        response = authenticated_admin_client.post(
            f"{BASE_URL}/api/masters/{MASTER_ID}/reset-notifications"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Admin can reset master's notification counter")


# Cleanup fixture to restore original state
@pytest.fixture(scope="module", autouse=True)
def cleanup(api_client, master_token):
    """Cleanup test data after all tests complete"""
    yield
    # Restore original telegram config (cleared)
    api_client.headers.update({"Authorization": f"Bearer {master_token}"})
    api_client.patch(
        f"{BASE_URL}/api/masters/{MASTER_ID}/telegram",
        json={
            "telegram_bot_token": None,
            "telegram_chat_id": None,
            "telegram_notifications_enabled": False
        }
    )
    print("\n✓ Cleanup: Telegram config restored to default state")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
