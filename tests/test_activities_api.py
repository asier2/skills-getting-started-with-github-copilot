import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, sample_activities):
        """Verify GET /activities returns all registered activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Test Activity" in data
        assert "Workshop A" in data
        assert "Workshop B" in data

    def test_get_activities_response_structure(self, client, sample_activities):
        """Verify activity response has correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Test Activity"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_empty_participants_initially(self, client, sample_activities):
        """Verify activities have empty participant lists initially."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert activity_info["participants"] == []


class TestRootRedirect:
    """Test suite for GET / (root) endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Verify root endpoint redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [307, 308]  # Temporary/permanent redirect
        assert "/static/index.html" in response.headers["location"]


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, sample_activities, test_email):
        """Verify successful signup adds student to activity."""
        activity_name = "Test Activity"
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert response.status_code == 200
        
        # Verify student was added
        activities = client.get("/activities").json()
        assert test_email in activities[activity_name]["participants"]

    def test_signup_multiple_activities(self, client, sample_activities, test_email):
        """Verify student can sign up for multiple activities."""
        email = test_email
        
        # Sign up for first activity
        response1 = client.post(
            f"/activities/Test Activity/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/Workshop A/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities = client.get("/activities").json()
        assert email in activities["Test Activity"]["participants"]
        assert email in activities["Workshop A"]["participants"]

    def test_signup_activity_not_found(self, client, sample_activities, test_email):
        """Verify signup returns 404 for non-existent activity."""
        response = client.post(
            f"/activities/NonExistent Activity/signup?email={test_email}"
        )
        assert response.status_code == 404

    def test_signup_duplicate_email_returns_400(self, client, sample_activities, test_email):
        """Verify duplicate signup returns 400 error."""
        activity_name = "Test Activity"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert response2.status_code == 400

    def test_signup_different_students_same_activity(self, client, sample_activities, test_email, another_email):
        """Verify multiple different students can sign up for same activity."""
        activity_name = "Test Activity"
        
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={another_email}"
        )
        assert response2.status_code == 200
        
        # Verify both are in the activity
        activities = client.get("/activities").json()
        assert len(activities[activity_name]["participants"]) == 2
        assert test_email in activities[activity_name]["participants"]
        assert another_email in activities[activity_name]["participants"]

    def test_signup_various_valid_emails(self, client, sample_activities):
        """Verify signup accepts various valid email formats."""
        valid_emails = [
            "user@mergington.edu",
            "first.last@mergington.edu",
            "user+tag@mergington.edu",
        ]
        
        for email in valid_emails:
            response = client.post(
                f"/activities/Test Activity/signup?email={email}"
            )
            assert response.status_code == 200


class TestUnregisterEndpoint:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, sample_activities, test_email):
        """Verify successful unregister removes student from activity."""
        activity_name = "Test Activity"
        
        # Sign up first
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # Unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert response.status_code == 200
        
        # Verify removed
        activities = client.get("/activities").json()
        assert test_email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client, sample_activities, test_email):
        """Verify unregister returns 404 for non-existent activity."""
        response = client.delete(
            f"/activities/NonExistent Activity/unregister?email={test_email}"
        )
        assert response.status_code == 404

    def test_unregister_student_not_signed_up_returns_400(self, client, sample_activities, test_email):
        """Verify unregister returns 400 when student is not signed up."""
        response = client.delete(
            f"/activities/Test Activity/unregister?email={test_email}"
        )
        assert response.status_code == 400

    def test_unregister_after_signup_then_unregister_again_returns_400(self, client, sample_activities, test_email):
        """Verify second unregister returns 400."""
        activity_name = "Test Activity"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        # First unregister
        response1 = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert response1.status_code == 200
        
        # Second unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert response2.status_code == 400

    def test_unregister_one_student_keeps_others(self, client, sample_activities, test_email, another_email):
        """Verify unregistering one student doesn't affect others."""
        activity_name = "Test Activity"
        
        # Sign up both students
        client.post(f"/activities/{activity_name}/signup?email={test_email}")
        client.post(f"/activities/{activity_name}/signup?email={another_email}")
        
        # Unregister first student
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert response.status_code == 200
        
        # Verify second student is still there
        activities = client.get("/activities").json()
        assert test_email not in activities[activity_name]["participants"]
        assert another_email in activities[activity_name]["participants"]
