"""
Shared pytest fixtures and configuration for FastAPI tests.

This module provides reusable fixtures for testing the Mergington High School
Activities Management System API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provides a TestClient instance for making HTTP requests to the FastAPI app.
    
    The client can be used to make requests like:
    - client.get("/activities")
    - client.post("/activities/{name}/signup?email=test@example.com")
    - client.delete("/activities/{name}/unregister?email=test@example.com")
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset the in-memory activities database before each test.
    
    This ensures test isolation by clearing participant lists and resetting
    to the initial state before each test runs. The 'autouse=True' parameter
    means this fixture runs automatically for every test.
    """
    # Reset each activity's participants list to initial state
    initial_state = {
        "Chess Club": ["michael@mergington.edu", "daniel@mergington.edu"],
        "Programming Class": ["emma@mergington.edu", "sophia@mergington.edu"],
        "Gym Class": ["john@mergington.edu", "olivia@mergington.edu"],
        "Basketball Team": ["alex@mergington.edu"],
        "Soccer Team": ["sarah@mergington.edu", "ryan@mergington.edu"],
        "Drama Club": ["julia@mergington.edu"],
        "Art Studio": ["maya@mergington.edu", "lucas@mergington.edu"],
        "Debate Team": ["chris@mergington.edu"],
        "Science Club": ["david@mergington.edu", "isabella@mergington.edu"]
    }
    
    for activity_name, initial_participants in initial_state.items():
        activities[activity_name]["participants"] = initial_participants.copy()
    
    yield
    
    # Cleanup after test (reset again to ensure clean state for next test)
    for activity_name, initial_participants in initial_state.items():
        activities[activity_name]["participants"] = initial_participants.copy()
