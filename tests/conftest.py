import os
from pathlib import Path
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = ROOT / "data" / f"test-suite-{uuid4().hex}.db"

os.environ["DATABASE_PATH"] = str(TEST_DATABASE)
os.environ["ADMIN_USER_NAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-admin-secret"
os.environ["RATE_LIMIT_ENABLED"] = "false"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    upload_dirs = [ROOT / "uploads" / "audio", ROOT / "uploads" / "kb"]
    before = {path: set(path.glob("*")) if path.exists() else set() for path in upload_dirs}
    with TestClient(app) as test_client:
        yield test_client

    for path in upload_dirs:
        if path.exists():
            for item in set(path.glob("*")) - before[path]:
                if item.is_file():
                    item.unlink(missing_ok=True)
    for suffix in ("", "-shm", "-wal"):
        Path(str(TEST_DATABASE) + suffix).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.core.rate_limit import reset_rate_limits_for_tests

    reset_rate_limits_for_tests()
    yield
    reset_rate_limits_for_tests()


@pytest.fixture
def auth_helpers(client):
    def register(role="tourist", prefix="user"):
        response = client.post(
            "/api/auth/register",
            json={
                "userName": f"{prefix}_{uuid4().hex[:10]}",
                "password": "secret123",
                "role": role,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    def guest(role="tourist", prefix="guest"):
        response = client.post(
            "/api/auth/guest",
            json={"displayName": f"{prefix}_{uuid4().hex[:10]}", "role": role},
        )
        assert response.status_code == 200, response.text
        return response.json()

    def headers(user):
        return {"Authorization": f"Bearer {user['token']}"}

    def create_room(guide):
        response = client.post(
            "/api/rooms",
            headers=headers(guide),
            json={
                "roomName": "Acceptance room",
                "scenicAreaId": "scenic_001",
                "routeId": "route_001",
            },
        )
        assert response.status_code == 200, response.text
        return response.json()["roomId"]

    return {
        "register": register,
        "guest": guest,
        "headers": headers,
        "create_room": create_room,
    }
