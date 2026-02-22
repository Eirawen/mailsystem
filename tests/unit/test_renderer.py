import pytest

from app.templates.renderer import render_template


def test_render_template_success():
    subject, html, text = render_template("Hi {{name}}", "<h1>{{name}}</h1>", None, {"name": "A"})
    assert subject == "Hi A"
    assert "A" in html
    assert "A" in text


def test_render_template_missing_variable_raises():
    with pytest.raises(Exception):
        render_template("Hi {{name}}", "<h1>{{name}}</h1>", None, {})
