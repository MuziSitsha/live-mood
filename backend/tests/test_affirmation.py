from fastapi.testclient import TestClient

import backend.main as main


client = TestClient(main.app)


def test_affirmation_success(monkeypatch):
    monkeypatch.setenv("HUGGING_FACE_API_KEY", "test-key")
    monkeypatch.setattr(
        main,
        "_generate_affirmation",
        lambda **_kwargs: "You are steady and capable today.",
    )

    response = client.post(
        "/api/affirmation",
        json={"name": "Amina", "feeling": "Hopeful", "details": "Starting fresh"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "affirmation" in body
    assert body["affirmation"]


def test_affirmation_requires_name_and_feeling(monkeypatch):
    monkeypatch.setenv("HUGGING_FACE_API_KEY", "test-key")
    monkeypatch.setattr(
        main,
        "_generate_affirmation",
        lambda **_kwargs: "You are steady and capable today.",
    )

    response = client.post("/api/affirmation", json={"name": "", "feeling": ""})

    assert response.status_code == 400


def test_affirmation_handles_upstream_error(monkeypatch):
    monkeypatch.setenv("HUGGING_FACE_API_KEY", "test-key")

    def _raise_error(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(main, "_generate_affirmation", _raise_error)

    response = client.post(
        "/api/affirmation",
        json={"name": "Amina", "feeling": "Hopeful", "details": ""},
    )

    assert response.status_code == 502
