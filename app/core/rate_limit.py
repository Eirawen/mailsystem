from redis import Redis


class RateLimitExceededError(RuntimeError):
    pass


class RateLimiter:
    def __init__(self, redis_client: Redis, window_seconds: int) -> None:
        self.redis = redis_client
        self.window_seconds = window_seconds

    def _consume(self, key: str, limit: int) -> None:
        count = self.redis.incr(key)
        if count == 1:
            self.redis.expire(key, self.window_seconds)
        if count > limit:
            raise RateLimitExceededError(f"rate limit exceeded for {key}")

    def check_tenant(self, tenant_id: str, limit: int) -> None:
        self._consume(f"rate:tenant:{tenant_id}", limit)

    def check_provider(self, tenant_id: str, provider: str, limit: int) -> None:
        self._consume(f"rate:provider:{tenant_id}:{provider}", limit)
