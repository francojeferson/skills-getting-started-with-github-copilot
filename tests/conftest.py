"""
Pytest configuration and fixtures for FastAPI application tests.
Provides a TestClient fixture with a fresh app instance for each test.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient with a fresh app instance for each test.
    Resets the in-memory activities database to initial state after each test.
    """
    # Store the initial state of activities
    initial_state = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()
        }
        for name, data in activities.items()
    }
    
    # Create and yield the test client
    client = TestClient(app)
    yield client
    
    # Reset activities to initial state after test completes
    for name, data in activities.items():
        activities[name]["participants"] = initial_state[name]["participants"].copy()
