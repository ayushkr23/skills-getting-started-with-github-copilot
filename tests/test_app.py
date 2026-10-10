from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_activity_page(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert response_activities.keys() == activities.keys()
    assert response_activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert response_activities["Soccer Club"]["participants"] == []


def test_signup_adds_participant(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Club"}
    assert email in client.get("/activities").json()["Soccer Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_unregistered_student(client):
    # Arrange
    activity = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}
