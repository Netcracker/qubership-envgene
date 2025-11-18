def ensure_required_keys(context: dict, required: list[str]):
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(
            f"Required variables: {', '.join(required)}. "
            f"Not found: {', '.join(missing)}"
        )


def ensure_valid_fields(context: dict, fields: list[str]):
    invalid = []
    for field in fields:
        value = context.get(field)
        if not value:
            invalid.append(f"{field}={value!r}")

    if invalid:
        raise ValueError(
            f"Invalid or empty fields found: {', '.join(invalid)}. "
            f"Required fields: {', '.join(fields)}"
        )
