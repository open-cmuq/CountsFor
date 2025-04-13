"""
This script contains the test cases for the endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

# ---------------------------
# Analytics Endpoints (from analytics router)
# ---------------------------

def test_analytics_course_coverage():
    # Test course coverage analytics; adjust sample parameters as needed.
    params = {"major": "CS", "semester": "F20"}
    response = client.get("/analytics/course-coverage", params=params)
    # Expect 200 if data exists, or 404 if no data
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        # Expect the response to be a dict with key "coverage"
        assert isinstance(data, dict)
        assert "coverage" in data
        assert isinstance(data["coverage"], list)

def test_analytics_enrollment_data():
    # Test enrollment data endpoint; adjust course_code to one you expect to exist
    params = {"course_code": "CS101"}
    response = client.get("/analytics/enrollment-data", params=params)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        # Expect the response to be a dict containing enrollment data, e.g., key "enrollment_data"
        # (Assuming EnrollmentDataResponse is defined accordingly.)
        # You may need to adjust this assertion based on your actual schema.
        assert isinstance(data, dict)
        # For example, if your schema is { "enrollment_data": [...] }
        assert "enrollment_data" in data

# ---------------------------
# Courses Endpoints (from courses router)
# ---------------------------

def test_search_courses():
    # Adjust these parameters exactly to your CombinedCourseFilter field names/types
    params = {
        "department": "CS",
        "semester": "F20",
        "has_prereqs": "true",        # if your filter expects a bool, "true" is usually parsed as True
        "cs_requirement": "Some CS Req",
        "search_query": "Introduction"  # rename from searchQuery to match your filter field
        # remove is_requirement, ba_requirement, bs_requirement, offered_pitts if they are not used or optional
        # or pass them if your filter expects them (but don't set them to None)
    }
    response = client.get("/courses/search", params=params)
    # With the fix, we should now get a 200 or 404
    assert response.status_code in (200, 404), f"Got {response.status_code} instead of 200 or 404"

def test_get_all_semesters():
    response = client.get("/courses/semesters")
    assert response.status_code == 200
    data = response.json()
    # Expecting a dict with key "semesters"
    assert "semesters" in data

def test_get_course_by_code():
    # Using a sample course code; adjust if necessary.
    response = client.get("/courses/CS101")
    assert response.status_code in (200, 404)

# ---------------------------
# Departments Endpoint (from departments router)
# ---------------------------

def test_get_departments():
    response = client.get("/departments")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        # Expect a dict with key "departments"
        assert isinstance(data, dict)
        assert "departments" in data

# ---------------------------
# Requirements Endpoints (from requirements router)
# ---------------------------

def test_get_requirements():
    response = client.get("/requirements")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        # Expect a dict with key "requirements"
        assert isinstance(data, dict)
        assert "requirements" in data
