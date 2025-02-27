import pytest
from app import app  # Import the Flask app
from unittest.mock import patch 
import asyncio
import json
import httpx


@pytest.fixture
def client():
    """Initialize the Flask test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# 1. Validate that the homepage loads correctly.
def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello, CI/CD!" in response.data.decode("utf-8")  

# 2. Ensure an invalid route returns a 404 error.
def test_404(client):
    response = client.get("/invalid-route")
    assert response.status_code == 404
    assert b"Page Not Found" in response.data

# 3. Validate that the performance endpoint returns a JSON response.
def test_performance_data(client):
    response = client.get("/performance-data")
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, dict)
    assert "cpu_usage" in json_data
    assert "memory_usage" in json_data
    assert "disk_usage" in json_data

# 4. Ensure that errors are logged properly.
def test_error_logging(client, caplog):
    with patch("app.psutil.cpu_percent", side_effect=Exception("Test Error")):
        response = client.get("/performance-data")
        assert response.status_code == 500
        assert "Error fetching performance metrics: Test Error" in caplog.text

# 5. Use pytest-benchmark to test response times.
def test_response_time(client, benchmark):
    result = benchmark(client.get, "/performance-data")
    assert result.status_code == 200

# 6. Session Management Test.
def test_session_management(client):
    with client.session_transaction() as session:
        session['user'] = 'test_user'

    response = client.get("/")
    assert session['user'] == 'test_user'


# 7. Load Testing for Multiple Concurrent Requests.
@pytest.mark.asyncio
async def test_concurrent_requests():
    async with httpx.AsyncClient() as client:
        async def fetch():
            response = await client.get("http://localhost:5050/performance")
            return response

        tasks = [fetch() for _ in range(10)]  # Simulate 10 concurrent requests
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200

# 8. Input Validation and Security Test.
def test_input_validation(client):
    malicious_payload = {"input": "<script>alert('XSS')</script>"}
    response = client.post("/api", data=json.dumps(malicious_payload), content_type="application/json")
    assert response.status_code in [400, 422]  # Should reject the request
    assert b"Invalid characters detected" in response.data

# 9. Health Check Endpoint Test.
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert b"Status: Operational" in response.data

# 10. Mock external dependencies using pytest-mock.
def test_mock_external_dependency(client, mocker):
    mocker.patch("app.psutil.cpu_percent", return_value=50)
    response = client.get("/performance-data")
    assert response.status_code == 200
    assert "50.00%" in response.get_json()["cpu_usage"]
