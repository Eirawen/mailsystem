import random


def compute_retry_delay(attempt: int, base_seconds: int, max_seconds: int) -> int:
    exp = base_seconds * (2 ** max(0, attempt - 1))
    bounded = min(exp, max_seconds)
    jitter = random.randint(0, max(1, bounded // 4))
    return bounded + jitter
