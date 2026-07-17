from unittest.mock import patch, MagicMock


def test_generate_prompt_dispatches_task_and_returns_task_id(auth_client):
    fake_result = MagicMock(id="fake-task-id")
    with patch("app.api.categories.generate_category_prompt_task.apply_async", return_value=fake_result) as apply_async:
        resp = auth_client.post(
            "/api/categories/generate-prompt",
            json={"name": "Technology", "keywords": ["ai"], "existing_categories": []},
        )

    assert resp.status_code == 200
    assert resp.json() == {"task_id": "fake-task-id"}
    apply_async.assert_called_once()
    assert apply_async.call_args.kwargs["queue"] == "process"


def test_generate_prompt_requires_a_name(auth_client):
    resp = auth_client.post("/api/categories/generate-prompt", json={"name": "   "})
    assert resp.status_code == 422


def test_generate_prompt_result_pending(auth_client):
    fake_async_result = MagicMock()
    fake_async_result.ready.return_value = False
    with patch("app.api.categories.AsyncResult", return_value=fake_async_result):
        resp = auth_client.get("/api/categories/generate-prompt/some-task-id")

    assert resp.status_code == 200
    assert resp.json() == {"status": "pending"}


def test_generate_prompt_result_done(auth_client):
    fake_async_result = MagicMock()
    fake_async_result.ready.return_value = True
    fake_async_result.failed.return_value = False
    fake_async_result.result = "Articles about technology and software."
    with patch("app.api.categories.AsyncResult", return_value=fake_async_result):
        resp = auth_client.get("/api/categories/generate-prompt/some-task-id")

    assert resp.status_code == 200
    assert resp.json() == {"status": "done", "prompt": "Articles about technology and software."}


def test_generate_prompt_result_failed(auth_client):
    fake_async_result = MagicMock()
    fake_async_result.ready.return_value = True
    fake_async_result.failed.return_value = True
    fake_async_result.result = Exception("Ollama unreachable")
    with patch("app.api.categories.AsyncResult", return_value=fake_async_result):
        resp = auth_client.get("/api/categories/generate-prompt/some-task-id")

    assert resp.status_code == 502
    assert "Ollama unreachable" in resp.json()["detail"]
