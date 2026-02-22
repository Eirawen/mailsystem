from app.core.config import get_settings
from app.providers.base import ProviderAdapter
from app.providers.mock_provider import MockProvider
from app.providers.smtp_provider import SMTPProvider


class ProviderRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self._providers: dict[str, ProviderAdapter] = {
            "smtp": SMTPProvider(settings=settings),
            "mock": MockProvider(),
        }

    def get(self, name: str) -> ProviderAdapter:
        provider = self._providers.get(name)
        if not provider:
            raise KeyError(f"unknown provider {name}")
        return provider


registry = ProviderRegistry()
