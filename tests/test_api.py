import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Healf Wellness Profiling Platform API"

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "healf-api"

def test_profile_init():
    """Test profile initialization"""
    user_id = "test_user_123"
    response = client.post(f"/api/v1/profile/init/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "profile" in data
    assert data["profile"]["user_id"] == user_id
    assert data["profile"]["completion_percentage"] == 0.0

def test_get_profile():
    """Test getting a profile"""
    user_id = "test_user_456"
    
    # First initialize the profile
    client.post(f"/api/v1/profile/init/{user_id}")
    
    # Then get the profile
    response = client.get(f"/api/v1/profile/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id

def test_get_nonexistent_profile():
    """Test getting a non-existent profile"""
    response = client.get("/api/v1/profile/nonexistent_user")
    assert response.status_code == 404

def test_update_profile():
    """Test updating a profile"""
    user_id = "test_user_789"
    
    # Initialize profile
    client.post(f"/api/v1/profile/init/{user_id}")
    
    # Update profile
    update_data = {
        "age": 25,
        "activity_level": "moderate",
        "gender": "female"
    }
    response = client.put(f"/api/v1/profile/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["profile"]["age"] == 25
    assert data["profile"]["activity_level"] == "moderate"
    assert data["profile"]["completion_percentage"] > 0

def test_profile_completion_status():
    """Test getting profile completion status"""
    user_id = "test_user_completion"
    
    # Initialize profile
    client.post(f"/api/v1/profile/init/{user_id}")
    
    # Get completion status
    response = client.get(f"/api/v1/profile/{user_id}/completion")
    assert response.status_code == 200
    data = response.json()
    assert "completion_percentage" in data
    assert "missing_fields" in data
    assert "completed_fields" in data
    assert "is_complete" in data

def test_delete_profile():
    """Test deleting a profile"""
    user_id = "test_user_delete"
    
    # Initialize profile
    client.post(f"/api/v1/profile/init/{user_id}")
    
    # Delete profile
    response = client.delete(f"/api/v1/profile/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Verify profile is deleted
    response = client.get(f"/api/v1/profile/{user_id}")
    assert response.status_code == 404 