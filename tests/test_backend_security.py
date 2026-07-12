import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.users import users


class TestBackendSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        suffix = uuid4().hex[:8]
        cls.guide = cls._register("guide_" + suffix, "guide")
        cls.tourist = cls._register("tourist_" + suffix, "tourist")
        cls.outsider = cls._register("outsider_" + suffix, "tourist")
        cls.guide_headers = cls._headers(cls.guide)
        cls.tourist_headers = cls._headers(cls.tourist)
        cls.outsider_headers = cls._headers(cls.outsider)

        response = cls.client.post(
            "/api/rooms",
            headers=cls.guide_headers,
            json={
                "roomName": "Security test",
                "scenicAreaId": "scenic_001",
                "routeId": "route_001",
            },
        )
        assert response.status_code == 200, response.text
        cls.room_id = response.json()["roomId"]

    @classmethod
    def _register(cls, name, role):
        response = cls.client.post(
            "/api/auth/register",
            json={"userName": name, "password": "secret123", "role": role},
        )
        assert response.status_code == 200, response.text
        return response.json()

    @staticmethod
    def _headers(user):
        return {"Authorization": "Bearer " + user["token"]}

    def test_password_is_hashed_and_login_is_verified(self):
        stored = users[self.guide["userId"]]
        self.assertNotIn("password", stored)
        self.assertTrue(stored["passwordHash"].startswith("pbkdf2_sha256$"))

        bad_login = self.client.post(
            "/api/auth/login",
            json={"userName": self.guide["userName"], "password": "wrong123"},
        )
        self.assertEqual(bad_login.status_code, 401)

        login = self.client.post(
            "/api/auth/login",
            json={"userName": self.guide["userName"], "password": "secret123"},
        )
        self.assertEqual(login.status_code, 200)

    def test_room_requires_membership_and_creator_is_leader_member(self):
        self.assertEqual(self.client.get("/api/rooms/" + self.room_id).status_code, 401)
        self.assertEqual(
            self.client.get("/api/rooms/" + self.room_id, headers=self.outsider_headers).status_code,
            403,
        )

        response = self.client.get("/api/rooms/" + self.room_id, headers=self.guide_headers)
        self.assertEqual(response.status_code, 200)
        room = response.json()
        self.assertEqual(room["leaderId"], self.guide["userId"])
        self.assertIn(self.guide["userId"], [member["userId"] for member in room["members"]])

    def test_only_leader_can_update_spot(self):
        join = self.client.post(
            "/api/rooms/" + self.room_id + "/join",
            headers=self.tourist_headers,
            json={},
        )
        self.assertEqual(join.status_code, 200)

        denied = self.client.post(
            "/api/rooms/" + self.room_id + "/current-spot",
            headers=self.tourist_headers,
            json={"spotId": "spot_001"},
        )
        self.assertEqual(denied.status_code, 403)

        updated = self.client.post(
            "/api/rooms/" + self.room_id + "/current-spot",
            headers=self.guide_headers,
            json={"spotId": "spot_001"},
        )
        self.assertEqual(updated.status_code, 200)

    def test_identity_spoofing_and_admin_access_are_rejected(self):
        forged = self.client.post(
            "/api/ai/public-question",
            headers=self.tourist_headers,
            json={
                "roomId": self.room_id,
                "userId": self.guide["userId"],
                "question": "test",
                "needAudio": False,
            },
        )
        self.assertEqual(forged.status_code, 403)
        self.assertEqual(self.client.get("/api/dashboard/overview").status_code, 401)
        self.assertEqual(
            self.client.get("/api/dashboard/overview", headers=self.tourist_headers).status_code,
            403,
        )


if __name__ == "__main__":
    unittest.main()
