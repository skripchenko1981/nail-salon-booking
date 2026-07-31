"""
Test suite for Promo Blocks CRUD operations
Tests the bug fix for promo blocks API (missing /api prefix)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://booking-app-demo-3.preview.emergentagent.com')

class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "admin"
        print(f"✓ Admin login successful, token received")
    
    def test_admin_login_invalid_credentials(self):
        """Test admin login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print(f"✓ Invalid credentials rejected with 401")


class TestPromoBlocksCRUD:
    """Promo blocks CRUD operations - tests the bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_promo_blocks_public(self):
        """Test public promo blocks endpoint"""
        response = requests.get(f"{BASE_URL}/api/promo-blocks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public promo blocks endpoint returns {len(data)} blocks")
    
    def test_get_promo_blocks_admin(self):
        """Test admin promo blocks endpoint (requires auth)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/promo-blocks",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin promo blocks endpoint returns {len(data)} blocks")
    
    def test_create_promo_block(self):
        """Test creating a new promo block - THIS WAS THE BUG"""
        payload = {
            "title": "TEST_Pytest Promo Block",
            "description": "Created by pytest to verify bug fix",
            "is_active": True,
            "position": 999
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/promo-blocks",
            json=payload,
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert "id" in data
        print(f"✓ Promo block created successfully with ID: {data['id']}")
        
        # Store ID for cleanup
        self.created_block_id = data["id"]
        
        # Verify by GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/promo-blocks",
            headers=self.headers
        )
        blocks = get_response.json()
        created_block = next((b for b in blocks if b["id"] == data["id"]), None)
        assert created_block is not None, "Created block not found in list"
        print(f"✓ Created block verified in list")
    
    def test_update_promo_block(self):
        """Test updating a promo block"""
        # First create a block
        create_response = requests.post(
            f"{BASE_URL}/api/admin/promo-blocks",
            json={
                "title": "TEST_Update Block",
                "description": "To be updated",
                "is_active": True,
                "position": 998
            },
            headers=self.headers
        )
        assert create_response.status_code == 200
        block_id = create_response.json()["id"]
        
        # Update the block
        update_payload = {
            "title": "TEST_Updated Block Title",
            "description": "Updated description"
        }
        update_response = requests.put(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            json=update_payload,
            headers=self.headers
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["title"] == update_payload["title"]
        print(f"✓ Promo block updated successfully")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            headers=self.headers
        )
    
    def test_toggle_visibility(self):
        """Test toggling promo block visibility"""
        # Create a block
        create_response = requests.post(
            f"{BASE_URL}/api/admin/promo-blocks",
            json={
                "title": "TEST_Toggle Block",
                "description": "To test visibility toggle",
                "is_active": True,
                "position": 997
            },
            headers=self.headers
        )
        assert create_response.status_code == 200
        block_id = create_response.json()["id"]
        
        # Toggle to hidden
        toggle_response = requests.put(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            json={"is_active": False},
            headers=self.headers
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["is_active"] == False
        print(f"✓ Block hidden successfully")
        
        # Toggle back to visible
        toggle_response = requests.put(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            json={"is_active": True},
            headers=self.headers
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["is_active"] == True
        print(f"✓ Block shown successfully")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            headers=self.headers
        )
    
    def test_delete_promo_block(self):
        """Test deleting a promo block"""
        # Create a block
        create_response = requests.post(
            f"{BASE_URL}/api/admin/promo-blocks",
            json={
                "title": "TEST_Delete Block",
                "description": "To be deleted",
                "is_active": True,
                "position": 996
            },
            headers=self.headers
        )
        assert create_response.status_code == 200
        block_id = create_response.json()["id"]
        
        # Delete the block
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/promo-blocks/{block_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        print(f"✓ Promo block deleted successfully")
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/admin/promo-blocks",
            headers=self.headers
        )
        blocks = get_response.json()
        deleted_block = next((b for b in blocks if b["id"] == block_id), None)
        assert deleted_block is None, "Deleted block still exists"
        print(f"✓ Deletion verified - block no longer in list")


class TestGalleryEndpoint:
    """Gallery endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        self.token = response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_gallery_public(self):
        """Test public gallery endpoint"""
        response = requests.get(f"{BASE_URL}/api/gallery")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public gallery endpoint returns {len(data)} images")
    
    def test_get_gallery_admin(self):
        """Test admin gallery endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/gallery",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin gallery endpoint returns {len(data)} images")


# Cleanup fixture to remove test data after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed promo blocks after all tests"""
    yield
    
    # Get token
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all blocks
    blocks_response = requests.get(
        f"{BASE_URL}/api/admin/promo-blocks",
        headers=headers
    )
    
    if blocks_response.status_code == 200:
        blocks = blocks_response.json()
        for block in blocks:
            if block.get("title", "").startswith("TEST_"):
                requests.delete(
                    f"{BASE_URL}/api/admin/promo-blocks/{block['id']}",
                    headers=headers
                )
                print(f"Cleaned up test block: {block['title']}")
