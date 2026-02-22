import hashlib
import hmac
import time

import pytest

from app.core.security import verify_webhook_signature


def test_verify_webhook_signature_success():
    payload = b'{"x":1}'
    ts = str(int(time.time()))
    secret = "abc"
    signature = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    verify_webhook_signature(payload, signature, ts, secret, replay_window_seconds=300)


def test_verify_webhook_signature_failure():
    with pytest.raises(Exception):
        verify_webhook_signature(b"x", "bad", str(int(time.time())), "abc", replay_window_seconds=300)
