from app.queue.retry_policy import compute_retry_delay


def test_retry_delay_is_bounded(monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 0)
    assert compute_retry_delay(1, 10, 900) == 10
    assert compute_retry_delay(2, 10, 900) == 20
    assert compute_retry_delay(20, 10, 900) == 900
