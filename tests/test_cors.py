"""
Test CORS middleware configuration.
Ensures that CORS headers are properly set for cross-origin requests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_cors_preflight_request(client):
    """
    Test that CORS preflight (OPTIONS) request returns correct headers.
    This simulates the browser's preflight request before making the actual request.
    """
    # Simulate a CORS preflight request
    response = client.options(
        "/api/v1/tenants/register",
        headers={
            "Origin": "http://frontend",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    
    # Check that preflight request is successful
    assert response.status_code == 200
    
    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


def test_cors_actual_request_headers(client):
    """
    Test that actual requests include CORS headers in the response.
    """
    # Make a request with Origin header
    response = client.get(
        "/health",
        headers={
            "Origin": "http://frontend"
        }
    )
    
    # Check that the response includes CORS headers
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # When credentials are allowed, the origin should be echoed back
    # or * should be present if all origins are allowed


def test_cors_allows_credentials(client):
    """
    Test that CORS configuration allows credentials.
    """
    response = client.options(
        "/api/v1/tenants/register",
        headers={
            "Origin": "http://frontend",
            "Access-Control-Request-Method": "POST",
        }
    )
    
    # Verify that credentials are allowed
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_with_different_origin(client):
    """
    Test CORS with a different origin to ensure it's handled correctly.
    """
    response = client.get(
        "/",
        headers={
            "Origin": "http://localhost:3000"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
