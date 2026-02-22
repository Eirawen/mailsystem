from app.queue.tasks_send import process_email_task


def test_send_api_accepted_and_idempotent(client, monkeypatch):
    monkeypatch.setattr(process_email_task, "apply_async", lambda *args, **kwargs: None)

    payload = {
        "tenant_id": "tenant-1",
        "recipient": {"email": "alice@example.com", "name": "Alice"},
        "template_id": "tpl-1",
        "variables": {"name": "Alice"},
        "metadata": {"source": "test"},
        "idempotency_key": "idem-1",
    }

    r1 = client.post("/send", json=payload)
    assert r1.status_code == 202
    body1 = r1.json()
    assert body1["idempotency_reused"] is False

    r2 = client.post("/send", json=payload)
    assert r2.status_code == 202
    body2 = r2.json()
    assert body2["idempotency_reused"] is True
    assert body2["email_id"] == body1["email_id"]
