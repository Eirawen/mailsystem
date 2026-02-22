def ensure_template_input(variables: dict) -> None:
    if not isinstance(variables, dict):
        raise ValueError("variables must be an object")
