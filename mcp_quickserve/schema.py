"""Generate JSON schemas from Python type hints and docstrings."""

from __future__ import annotations

import inspect
import typing
from typing import Any, Callable, get_type_hints


# Mapping of Python types to JSON Schema types
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _resolve_type(annotation: Any) -> dict[str, Any]:
    """Convert a Python type annotation to a JSON Schema type descriptor."""
    origin = typing.get_origin(annotation)

    if annotation in _TYPE_MAP:
        return {"type": _TYPE_MAP[annotation]}

    if annotation is type(None):
        return {"type": "null"}

    if origin is list:
        args = typing.get_args(annotation)
        items = _resolve_type(args[0]) if args else {}
        return {"type": "array", "items": items}

    if origin is dict:
        args = typing.get_args(annotation)
        schema: dict[str, Any] = {"type": "object"}
        if args and len(args) == 2:
            schema["additionalProperties"] = _resolve_type(args[1])
        return schema

    if origin is typing.Union:
        args = typing.get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            # Optional[X] case
            result = _resolve_type(non_none[0])
            result["nullable"] = True
            return result
        return {"anyOf": [_resolve_type(a) for a in args]}

    # Fallback
    return {"type": "string"}


def _parse_docstring_params(docstring: str | None) -> dict[str, str]:
    """Extract parameter descriptions from a docstring.

    Supports simple formats like:
        param_name: description text
        param_name -- description text
    """
    if not docstring:
        return {}

    descriptions: dict[str, str] = {}
    lines = docstring.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        # Match "param_name: description" or "param_name -- description"
        for separator in [":", " -- ", " - "]:
            if separator in stripped:
                parts = stripped.split(separator, 1)
                name = parts[0].strip().lstrip("-").strip()
                if name.isidentifier() and len(parts) > 1:
                    descriptions[name] = parts[1].strip()
                break

    return descriptions


def generate_schema(func: Callable) -> dict[str, Any]:
    """Generate a JSON Schema for a function's input parameters.

    Reads type hints and docstrings to produce a schema compatible
    with the MCP tool input_schema format.

    Args:
        func: The function to generate a schema for.

    Returns:
        A dictionary representing the JSON Schema.
    """
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    doc_params = _parse_docstring_params(func.__doc__)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name == "self" or name == "cls":
            continue

        annotation = hints.get(name, str)
        prop = _resolve_type(annotation)

        if name in doc_params:
            prop["description"] = doc_params[name]

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            prop["default"] = param.default

        properties[name] = prop

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    return schema
