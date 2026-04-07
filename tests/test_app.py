"""
Integration tests for FastAPI activities API using AAA (Arrange-Act-Assert) pattern.
Tests cover all endpoints: redirect, activities list, signup, and unregister.
"""

import pytest
from fastapi.testclient import TestClient


class TestRedirect:
    """Test the root endpoint redirect to static HTML."""
    
    def test_root_redirects_to_static_index(self, client):
        """
        ARRANGE: TestClient is ready
        ACT: Make GET request to root endpoint
        ASSERT: Verify 307 redirect to /static/index.html
        """
        # ACT
        response = client.get("/", follow_redirects=False)
        
        # ASSERT
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesList:
    """Test the activities list endpoint."""
    
    def test_get_all_activities_returns_nine_activities(self, client):
        """
        ARRANGE: TestClient is ready
        ACT: Make GET request to /activities
        ASSERT: Verify response contains all 9 activities with correct structure
        """
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        
    def test_activities_have_required_fields(self, client):
        """
        ARRANGE: TestClient is ready
        ACT: Make GET request to /activities
        ASSERT: Verify each activity has required fields
        """
        # ACT
        response = client.get("/activities")
        activities = response.json()
        
        # ASSERT
        required_fields = {"description", "schedule", "max_participants", "participants"}
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert required_fields.issubset(set(activity_data.keys()))
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_activities_contain_initial_participants(self, client):
        """
        ARRANGE: TestClient is ready
        ACT: Get activities and check specific activity participants
        ASSERT: Verify initial participants are present (Chess Club has 2)
        """
        # ACT
        response = client.get("/activities")
        activities = response.json()
        
        # ASSERT
        assert "Chess Club" in activities
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]


class TestSignup:
    """Test the signup endpoint with various scenarios."""
    
    def test_signup_success_new_student(self, client):
        """
        ARRANGE: Student email not in Programming Class participants
        ACT: Sign up new student for Programming Class
        ASSERT: Verify 200 response and student added to participants
        """
        # ARRANGE
        test_email = "newtestuser@example.com"
        activity_name = "Programming Class"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert test_email in response.json()["message"]
        
        # Verify student was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """
        ARRANGE: Non-existent activity name
        ACT: Attempt to sign up for invalid activity
        ASSERT: Verify 404 response
        """
        # ARRANGE
        test_email = "test@example.com"
        invalid_activity = "Non-existent Activity"
        
        # ACT
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_student(self, client):
        """
        ARRANGE: Student already signed up for Chess Club
        ACT: Attempt to sign up same student again
        ASSERT: Verify 400 response with duplicate error
        """
        # ARRANGE
        activity_name = "Chess Club"
        existing_student = "michael@mergington.edu"  # Already in Chess Club
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_student}
        )
        
        # ASSERT
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_missing_email_parameter(self, client):
        """
        ARRANGE: No email parameter provided
        ACT: POST to signup without email query parameter
        ASSERT: Verify 422 Unprocessable Entity (validation error)
        """
        # ARRANGE
        activity_name = "Art Club"
        
        # ACT
        response = client.post(f"/activities/{activity_name}/signup")
        
        # ASSERT
        assert response.status_code == 422  # Validation error
    
    def test_signup_multiple_activities_same_student(self, client):
        """
        ARRANGE: Student signs up for first activity
        ACT: Sign same student up for different activity
        ASSERT: Verify student can be in multiple activities
        """
        # ARRANGE
        test_email = "multiactivity@example.com"
        activity1 = "Chess Club"
        activity2 = "Art Club"
        
        # ACT - Sign up for first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": test_email}
        )
        
        # ACT - Sign up for second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email in activities[activity1]["participants"]
        assert test_email in activities[activity2]["participants"]


class TestUnregister:
    """Test the unregister endpoint with various scenarios."""
    
    def test_unregister_success_existing_student(self, client):
        """
        ARRANGE: Student signs up for activity
        ACT: Unregister that student from activity
        ASSERT: Verify 200 response and student removed from participants
        """
        # ARRANGE
        test_email = "unregtest@example.com"
        activity_name = "Drama Club"
        
        # Set up: Sign up the student first
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify student was actually removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert test_email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """
        ARRANGE: Non-existent activity name
        ACT: Attempt to unregister from invalid activity
        ASSERT: Verify 404 response
        """
        # ARRANGE
        test_email = "test@example.com"
        invalid_activity = "Fake Activity"
        
        # ACT
        response = client.post(
            f"/activities/{invalid_activity}/unregister",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_registered(self, client):
        """
        ARRANGE: Student never signed up for activity
        ACT: Attempt to unregister student not in participants list
        ASSERT: Verify 400 response
        """
        # ARRANGE
        test_email = "never_signed_up@example.com"
        activity_name = "Tennis Club"
        
        # ACT
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_missing_email_parameter(self, client):
        """
        ARRANGE: No email parameter provided
        ACT: POST to unregister without email query parameter
        ASSERT: Verify 422 Unprocessable Entity (validation error)
        """
        # ARRANGE
        activity_name = "Science Club"
        
        # ACT
        response = client.post(f"/activities/{activity_name}/unregister")
        
        # ASSERT
        assert response.status_code == 422  # Validation error
    
    def test_unregister_sequence_signup_then_unregister(self, client):
        """
        ARRANGE: Student signs up for activity
        ACT: Unregister student from activity, then attempt to unregister again
        ASSERT: First unregister succeeds, second fails with 400
        """
        # ARRANGE
        test_email = "sequence@example.com"
        activity_name = "Robotics Club"
        
        # Set up: Sign up the student
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # ACT - First unregister (should succeed)
        response1 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # ACT - Second unregister (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # ASSERT
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]


class TestIntegrationScenarios:
    """Test complex integration scenarios combining multiple endpoints."""
    
    def test_full_signup_and_unregister_workflow(self, client):
        """
        ARRANGE: Multiple students and activities ready
        ACT: Student signs up, verify in list, then unregisters
        ASSERT: All operations succeed and state changes correctly
        """
        # ARRANGE
        test_email = "workflow@example.com"
        activity_name = "Basketball Team"
        
        # ACT 1: Verify initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # ACT 2: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # ASSERT signup worked
        assert signup_response.status_code == 200
        response = client.get("/activities")
        after_signup = len(response.json()[activity_name]["participants"])
        assert after_signup == initial_count + 1
        
        # ACT 3: Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        # ASSERT unregister worked
        assert unregister_response.status_code == 200
        response = client.get("/activities")
        final_count = len(response.json()[activity_name]["participants"])
        assert final_count == initial_count
    
    def test_different_students_same_activity(self, client):
        """
        ARRANGE: Multiple students
        ACT: Signup different students for same activity
        ASSERT: All succeed and activity shows all participants
        """
        # ARRANGE
        activity_name = "Gym Class"
        students = ["student1@example.com", "student2@example.com", "student3@example.com"]
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # ACT
        for student_email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # ASSERT
        response = client.get("/activities")
        final_count = len(response.json()[activity_name]["participants"])
        assert final_count == initial_count + len(students)
        
        for student_email in students:
            assert student_email in response.json()[activity_name]["participants"]
