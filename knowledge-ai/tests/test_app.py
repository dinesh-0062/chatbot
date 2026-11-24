import os

os.environ.setdefault("INITIALIZE_DATABASE", "false")

from fastapi.testclient import TestClient

from app.main import app
from app.services.url_validator import UnsafeURLException, validate_public_http_url


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_rejects_localhost_url():
    try:
        validate_public_http_url("http://localhost/admin")
        assert False, "localhost URL should be rejected"
    except UnsafeURLException:
        assert True


def test_rejects_private_url():
    try:
        validate_public_http_url("http://127.0.0.1/admin")
        assert False, "private URL should be rejected"
    except UnsafeURLException:
        assert True


def test_rejects_invalid_scheme():
    try:
        validate_public_http_url("file:///etc/passwd")
        assert False, "non-HTTP URL should be rejected"
    except UnsafeURLException:
        assert True
