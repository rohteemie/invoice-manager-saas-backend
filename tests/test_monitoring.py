"""
Tests for monitoring endpoints (health check and metrics).
"""


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_metrics_endpoint(client):
    """Test the Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Metrics should be in plain text format
    assert "text/plain" in response.headers["content-type"]
    # Should contain some basic metrics
    content = response.text
    assert "http_requests" in content or "HELP" in content


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/docs"
