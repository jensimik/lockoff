from fastapi.testclient import TestClient


def test_healthz(client: TestClient):
    response = client.get("/healtz")
    assert response.status_code == 200
