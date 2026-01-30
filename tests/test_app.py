"""
Test suite for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self):
        """Test that all expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        expected = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Math Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        for activity in expected:
            assert activity in activities
    
    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing field {field}"
    
    def test_participants_is_list(self):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""
    
    def test_signup_with_valid_activity_and_email(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Basketball Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]
    
    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds participant to activity"""
        email = "test_signup@mergington.edu"
        response = client.post(
            f"/activities/Soccer Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities["Soccer Club"]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_duplicate_signup_returns_400(self):
        """Test that duplicate signup returns 400 error"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Art Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()
    
    def test_signup_response_format(self):
        """Test that signup response has correct format"""
        response = client.post(
            "/activities/Drama Club/signup?email=drama@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_removes_participant(self):
        """Test that unregister removes a participant"""
        email = "to_remove@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Debate Team/signup?email={email}")
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities["Debate Team"]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/Debate Team/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email not in activities["Debate Team"]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregister for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_unregister_non_registered_student_returns_400(self):
        """Test unregister for student not registered returns 400"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_response_format(self):
        """Test that unregister response has correct format"""
        email = "unreg@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Math Club/signup?email={email}")
        
        # Unregister
        response = client.post(
            f"/activities/Math Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 303, 307, 308]
        assert "/static" in response.headers.get("location", "").lower()


class TestDataIntegrity:
    """Tests to ensure data integrity across operations"""
    
    def test_max_participants_respected(self):
        """Test that max_participants values are consistent"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            participants = activity_data["participants"]
            # Participants should not exceed max_participants
            assert len(participants) <= max_participants
    
    def test_no_duplicate_participants(self):
        """Test that no duplicates exist in participants list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participants = activity_data["participants"]
            assert len(participants) == len(set(participants)), \
                f"Duplicate participants in {activity_name}"
