import pytest
from fastapi.testclient import TestClient
import redis
import json
import time

from app.main import app

client = TestClient(app)

REDIS_HOST = "localhost"
REDIS_PORT = 6379


@pytest.fixture
def auth_token():
    client.post("/auth/register", json={
        "username": "testuser", "email": "test@test.tn", "password": "Test1234!"
    })
    resp = client.post("/auth/login", json={
        "username": "testuser", "password": "Test1234!"
    })
    data = resp.json()
    # Votre API retourne la clé "token"
    return data.get("token", "")


def test_auth_register_login():
    resp = client.post("/auth/register", json={
        "username": "newuser", "email": "new@test.tn", "password": "New1234!"
    })
    assert resp.status_code in (200, 201, 400)


def test_recherche_avis(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/recherche_avis?mot_cle=Mytek&limit=5", headers=headers)
    assert resp.status_code == 200

def test_worker_async():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.delete("sentiment_tasks", "sentiment_results")
    r.lpush("sentiment_tasks", json.dumps({"text": "Excellent produit"}))
    time.sleep(5)
    result = r.lpop("sentiment_results")
    assert result is not None
