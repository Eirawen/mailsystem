import hashlib
import hmac
import time


class SignatureVerificationError(ValueError):
    pass


def verify_webhook_signature(
    payload: bytes,
    provided_signature: str,
    timestamp: str,
    secret: str,
    replay_window_seconds: int,
) -> None:
    if not secret:
        raise SignatureVerificationError("webhook secret is not configured")

    try:
        ts = int(timestamp)
    except (TypeError, ValueError) as exc:
        raise SignatureVerificationError("invalid timestamp") from exc

    now = int(time.time())
    if abs(now - ts) > replay_window_seconds:
        raise SignatureVerificationError("timestamp outside replay window")

    signing_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signing_payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, provided_signature):
        raise SignatureVerificationError("invalid signature")
