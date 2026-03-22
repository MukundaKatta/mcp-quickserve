"""Input validation engine for MCP tool calls."""

from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")


_JSON_TYPE_CHECKS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def validate_input(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate input data against a JSON Schema.

    Checks required fields, types, and applies defaults for missing
    optional fields.

    Args:
        data: The input data to validate.
        schema: The JSON Schema to validate against.

    Returns:
        The validated (and possibly enriched with defaults) data.

    Raises:
        ValidationError: If validation fails.
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    validated: dict[str, Any] = {}

    # Check required fields
    for field in required:
        if field not in data:
            raise ValidationError(field, "required field is missing")

    # Validate each property
    for field, field_schema in properties.items():
        if field in data:
            value = data[field]
            _validate_field(field, value, field_schema)
            validated[field] = value
        elif "default" in field_schema:
            validated[field] = field_schema["default"]
        elif field in required:
            raise ValidationError(field, "required field is missing")

    return validated


def _validate_field(field: str, value: Any, field_schema: dict[str, Any]) -> None:
    """Validate a single field value against its schema."""
    # Handle nullable
    if value is None and field_schema.get("nullable"):
        return

    expected_type = field_schema.get("type")
    if not expected_type:
        return

    # Type check
    checker = _JSON_TYPE_CHECKS.get(expected_type)
    if checker and not isinstance(value, checker):
        raise ValidationError(
            field,
            f"expected type '{expected_type}', got '{type(value).__name__}'"
        )

    # Array items validation
    if expected_type == "array" and "items" in field_schema:
        items_schema = field_schema["items"]
        for i, item in enumerate(value):
            _validate_field(f"{field}[{i}]", item, items_schema)
