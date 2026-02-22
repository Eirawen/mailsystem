import re

from jinja2 import Environment, StrictUndefined

from app.templates.validators import ensure_template_input


env = Environment(undefined=StrictUndefined, autoescape=True)


def html_to_text(html: str) -> str:
    stripped = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", "", stripped)
    return re.sub(r"\n{3,}", "\n\n", stripped).strip()


def render_template(subject_template: str, html_template: str, text_template: str | None, variables: dict) -> tuple[str, str, str]:
    ensure_template_input(variables)
    subject = env.from_string(subject_template).render(**variables)
    html = env.from_string(html_template).render(**variables)
    if text_template:
        text = env.from_string(text_template).render(**variables)
    else:
        text = html_to_text(html)
    return subject, html, text
