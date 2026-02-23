import copy
import pytest
from fastapi.testclient import TestClient

from src import app

# Keep a deep copy of the original activities so tests can restore state.
_ORIGINAL_ACTIVITIES = copy.deepcopy(app.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the global activities dictionary before each test."""
    app.activities = copy.deepcopy(_ORIGINAL_ACTIVITIES)


@pytest.fixture
def client():
    """FastAPI test client for making requests against the app."""
    return TestClient(app.app)


def test_root_redirects(client):
    # Arrange: client fixture provides a ready TestClient
    # Act
    resp = client.get("/")
    # Assert
    assert resp.status_code in (307, 200)
    # FastAPI's TestClient follows redirects by default, so check final URL
    assert "/static/index.html" in str(resp.url)


def test_get_activities_returns_initial_data(client):
    # Arrange: initial state is already arranged by reset_activities
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    assert resp.json() == _ORIGINAL_ACTIVITIES


def test_signup_adds_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    # Act
    resp = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    # Assert
    assert resp.status_code == 200
    assert email in app.activities[activity]["participants"]


def test_signup_already_registered(client):
    # Arrange
    activity = "Chess Club"
    email = _ORIGINAL_ACTIVITIES[activity]["participants"][0]
    # Act
    resp = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    # Assert
    assert resp.status_code == 400


def test_signup_activity_not_found(client):
    # Act
    resp = client.post("/activities/NoSuch/signup", params={"email": "x@y"})
    # Assert
    assert resp.status_code == 404


def test_remove_signup_removes_participant(client):
    # Arrange
    activity = "Programming Class"
    email = _ORIGINAL_ACTIVITIES[activity]["participants"][0]
    # Act
    resp = client.delete(
        f"/activities/{activity}/signup", params={"email": email}
    )
    # Assert
    assert resp.status_code == 200
    assert email not in app.activities[activity]["participants"]


def test_remove_signup_activity_not_found(client):
    # Act
    resp = client.delete("/activities/NoSuch/signup", params={"email": "foo@bar"})
    # Assert
    assert resp.status_code == 404


def test_remove_signup_not_registered(client):
    # Arrange
    activity = "Chess Club"
    email = "absent@mergington.edu"
    # Act
    resp = client.delete(
        f"/activities/{activity}/signup", params={"email": email}
    )
    # Assert
    assert resp.status_code == 404
