# pylint: disable=missing-module-docstring
"""
This script contains the test cases for the departments endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

# ---------------------------
# Departments Endpoint (from departments router)
# ---------------------------

def test_get_departments():
    """
    Test get departments endpoint
    """
    response = client.get("/departments")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "departments" in data
        assert isinstance(data["departments"], list)
        if data["departments"]:
            dept = data["departments"][0]
            assert isinstance(dept, dict)
            assert "dep_code" in dept
            assert "name" in dept