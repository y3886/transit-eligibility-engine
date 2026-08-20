import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_resolve_endpoint(client):
    resp = client.post("/resolve", json={"address": "תל אביב"})
    assert resp.status_code in (200, 503)
