# pylint: disable=missing-module-docstring
"""
This script contains the test cases for the requirements endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

# ---------------------------
# Requirements Endpoints (from requirements router)
# ---------------------------

def test_get_requirements():
    """
    Test get requirements endpoint
    """
    response = client.get("/requirements")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()

        assert isinstance(data, dict)
        assert "requirements" in data
        assert isinstance(data["requirements"], list)

        if data["requirements"]:
            req = data["requirements"][0]
            assert isinstance(req, dict)
            assert "requirement" in req
            assert "type" in req
            assert "major" in req
            assert isinstance(req["type"], bool)