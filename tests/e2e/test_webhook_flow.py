import hashlib
import hmac
import json
import time


def test_webhook_endpoint_accepts_signed_event(client):
    ts = str(int(time.time()))
    payload = {
        "tenant_id": "tenant-1",
        "email_id": "missing-email",
        "event_type": "delivered",
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = hmac.new(b"test-secret", f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()

    r = client.post(
        "/webhooks/mock",
        data=raw,
        headers={"X-Signature": sig, "X-Timestamp": ts, "X-Event-Id": "evt-1", "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
