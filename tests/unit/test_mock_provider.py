from app.providers.base import EmailMessage
from app.providers.mock_provider import MockProvider


def test_mock_provider_success():
    provider = MockProvider()
    resp = provider.send(
        EmailMessage(
            email_id="e1",
            tenant_id="t1",
            to_email="user@example.com",
            to_name=None,
            subject="s",
            html_body="<p>x</p>",
            text_body="x",
            metadata={},
        )
    )
    assert resp.accepted is True
    assert resp.provider_message_id


def test_mock_provider_forced_failure():
    provider = MockProvider()
    resp = provider.send(
        EmailMessage(
            email_id="e1",
            tenant_id="t1",
            to_email="user@fail.example",
            to_name=None,
            subject="s",
            html_body="<p>x</p>",
            text_body="x",
            metadata={},
        )
    )
    assert resp.accepted is False
    assert resp.transient is False
