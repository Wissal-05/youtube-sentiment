"""Tests de l'API FastAPI (phase 7 : /health, /predict_batch, erreurs, temps de réponse)."""
import time

import pytest
from fastapi.testclient import TestClient

from app_api import app


@pytest.fixture(scope="module")
def client():
    # Le "with" déclenche le chargement du modèle (lifespan)
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_batch_basic(client):
    comments = ["I love this video", "This is terrible", "It is a video about cats"]
    r = client.post("/predict_batch", json={"comments": comments})
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == 3
    assert "statistics" in body
    assert "processing_time_ms" in body
    for p in body["predictions"]:
        assert 0.0 <= p["confidence"] <= 1.0


@pytest.mark.parametrize("n", [1, 10, 50, 200])
def test_predict_batch_sizes(client, n):
    comments = ["this is a great video, thanks"] * n
    r = client.post("/predict_batch", json={"comments": comments})
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == n


def test_empty_batch(client):
    r = client.post("/predict_batch", json={"comments": []})
    assert r.status_code == 422


def test_invalid_payload(client):
    r = client.post("/predict_batch", json={"wrong_field": 123})
    assert r.status_code == 422


def test_invalid_type(client):
    r = client.post("/predict_batch", json={"comments": "pas une liste"})
    assert r.status_code == 422


def test_cors_header(client):
    r = client.get("/health", headers={"Origin": "chrome-extension://abc"})
    assert r.headers.get("access-control-allow-origin") in ("*", "chrome-extension://abc")


def test_response_time_batch_50(client):
    comments = ["this is a great video"] * 50
    client.post("/predict_batch", json={"comments": comments})  # échauffement
    start = time.perf_counter()
    r = client.post("/predict_batch", json={"comments": comments})
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert r.status_code == 200
    print(f"\nTemps de réponse total (batch de 50) : {elapsed_ms:.1f} ms")
    assert elapsed_ms < 500