"""
Integration tests for the Mergington High School Activities Management System.

These tests verify that the FastAPI endpoints work correctly by making actual
HTTP requests through the TestClient. They cover happy paths, error cases, and
edge cases for all three main endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9

    def test_get_activities_contains_all_expected_activities(self, client):
        """Test that all 9 expected activities are present"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Team",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity in data.items():
            for field in required_fields:
                assert field in activity, f"{activity_name} missing {field}"
                
    def test_activity_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert isinstance(activity["participants"], list), \
                f"{activity_name} participants should be a list"

    def test_activity_max_participants_is_positive_integer(self, client):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            max_part = activity["max_participants"]
            assert isinstance(max_part, int) and max_part > 0, \
                f"{activity_name} max_participants should be positive integer"

    def test_get_activities_includes_initial_participants(self, client):
        """Test that activities include their initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert "sarah@mergington.edu" in data["Soccer Team"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_student_added_to_participants_after_signup(self, client):
        """Test that student is actually added to the activity's participants"""
        email = "newstudent@mergington.edu"
        
        # Sign up
        client.post("/activities/Chess Club/signup", params={"email": email})
        
        # Verify student was added
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email in participants

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_duplicate_signup_returns_400(self, client):
        """Test that signing up for the same activity twice returns 400"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_signup_with_different_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multi@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_with_empty_email_parameter(self, client):
        """Test signup with empty email parameter"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        
        # Empty email is technically a valid parameter value, but the API doesn't validate it
        # This test documents current behavior
        assert response.status_code == 200

    def test_signup_without_email_parameter(self, client):
        """Test signup without email parameter returns error"""
        response = client.post(
            "/activities/Chess Club/signup"
        )
        
        # Missing required query parameter
        assert response.status_code == 422

    def test_activity_name_is_case_sensitive(self, client):
        """Test that activity name lookup is case-sensitive"""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404

    def test_signup_response_includes_email_and_activity_name(self, client):
        """Test that response message includes both email and activity name"""
        email = "verify@mergington.edu"
        activity = "Basketball Team"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        message = response.json()["message"]
        assert email in message
        assert activity in message

    def test_multiple_students_can_signup_for_same_activity(self, client):
        """Test that multiple different students can signup for the same activity"""
        activity = "Drama Club"
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        participants = client.get("/activities").json()[activity]["participants"]
        for email in students:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]

    def test_student_removed_from_participants_after_unregister(self, client):
        """Test that student is actually removed from activity's participants"""
        email = "michael@mergington.edu"
        
        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Verify student was removed
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_registered_returns_400(self, client):
        """Test that unregistering a non-registered student returns 400"""
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_then_reregister_succeeds(self, client):
        """Test that a student can unregister and then re-register"""
        email = "testuser@mergington.edu"
        activity = "Soccer Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Unregister
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Re-register
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify in activity
        participants = client.get("/activities").json()[activity]["participants"]
        assert email in participants

    def test_unregister_with_empty_email_parameter(self, client):
        """Test unregister with empty email parameter"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": ""}
        )
        
        # Empty email won't match any registered student
        assert response.status_code == 400

    def test_unregister_without_email_parameter(self, client):
        """Test unregister without email parameter returns error"""
        response = client.delete(
            "/activities/Chess Club/unregister"
        )
        
        # Missing required query parameter
        assert response.status_code == 422

    def test_unregister_response_includes_email_and_activity_name(self, client):
        """Test that response message includes both email and activity name"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        message = response.json()["message"]
        assert email in message
        assert activity in message

    def test_activity_name_is_case_sensitive_on_unregister(self, client):
        """Test that activity name lookup is case-sensitive for unregister"""
        response = client.delete(
            "/activities/chess club/unregister",  # lowercase
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 404

    def test_double_unregister_fails_on_second_attempt(self, client):
        """Test that trying to unregister twice fails on the second attempt"""
        email = "david@mergington.edu"
        activity = "Science Club"
        
        # First unregister succeeds
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister fails
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]


class TestEndpointIntegration:
    """Tests for interactions between different endpoints"""

    def test_signup_and_get_activities_reflect_changes(self, client):
        """Test that changes from signup are reflected in get_activities"""
        email = "integration@mergington.edu"
        activity = "Debate Team"
        
        # Initial check - not registered
        initial = client.get("/activities").json()
        assert email not in initial[activity]["participants"]
        
        # Sign up
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Check again - should be registered
        after_signup = client.get("/activities").json()
        assert email in after_signup[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister", params={"email": email})
        
        # Check again - should not be registered
        after_unregister = client.get("/activities").json()
        assert email not in after_unregister[activity]["participants"]

    def test_multiple_operations_sequence(self, client):
        """Test a sequence of signup and unregister operations"""
        activities_to_try = ["Chess Club", "Drama Club", "Art Studio"]
        email = "sequence@mergington.edu"
        
        # Sign up for all
        for activity in activities_to_try:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all
        data = client.get("/activities").json()
        for activity in activities_to_try:
            assert email in data[activity]["participants"]
        
        # Unregister from all
        for activity in activities_to_try:
            response = client.delete(
                f"/activities/{activity}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all removed
        data = client.get("/activities").json()
        for activity in activities_to_try:
            assert email not in data[activity]["participants"]

    def test_concurrent_signups_dont_duplicate(self, client):
        """Test that participant counts are correct with multiple operations"""
        activity = "Basketball Team"
        emails = ["user1@test.com", "user2@test.com", "user3@test.com"]
        
        # Get initial count
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])
        
        # Sign up three users
        for email in emails:
            client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Verify count increased by 3
        final = client.get("/activities").json()
        final_count = len(final[activity]["participants"])
        assert final_count == initial_count + 3
