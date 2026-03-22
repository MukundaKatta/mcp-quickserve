"""Tests for mcp-quickserve core functionality."""

import asyncio
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_quickserve import Server, generate_schema, validate_input
from mcp_quickserve.validation import ValidationError


class TestSchemaGeneration(unittest.TestCase):
    """Test JSON schema generation from type hints."""

    def test_simple_types(self):
        def func(name: str, age: int, score: float, active: bool) -> str:
            pass

        schema = generate_schema(func)
        self.assertEqual(schema["properties"]["name"]["type"], "string")
        self.assertEqual(schema["properties"]["age"]["type"], "integer")
        self.assertEqual(schema["properties"]["score"]["type"], "number")
        self.assertEqual(schema["properties"]["active"]["type"], "boolean")

    def test_required_fields(self):
        def func(required_param: str, optional_param: str = "default") -> str:
            pass

        schema = generate_schema(func)
        self.assertIn("required_param", schema["required"])
        self.assertNotIn("optional_param", schema["required"])

    def test_default_values(self):
        def func(x: int = 42) -> int:
            pass

        schema = generate_schema(func)
        self.assertEqual(schema["properties"]["x"]["default"], 42)

    def test_list_type(self):
        def func(items: list[str]) -> list:
            pass

        schema = generate_schema(func)
        self.assertEqual(schema["properties"]["items"]["type"], "array")
        self.assertEqual(schema["properties"]["items"]["items"]["type"], "string")

    def test_dict_type(self):
        def func(data: dict[str, int]) -> dict:
            pass

        schema = generate_schema(func)
        self.assertEqual(schema["properties"]["data"]["type"], "object")


class TestValidation(unittest.TestCase):
    """Test input validation."""

    def test_valid_input(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        result = validate_input({"name": "Alice", "age": 30}, schema)
        self.assertEqual(result["name"], "Alice")
        self.assertEqual(result["age"], 30)

    def test_missing_required(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        with self.assertRaises(ValidationError):
            validate_input({}, schema)

    def test_wrong_type(self):
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        with self.assertRaises(ValidationError):
            validate_input({"count": "not a number"}, schema)

    def test_default_applied(self):
        schema = {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
            "required": [],
        }
        result = validate_input({}, schema)
        self.assertEqual(result["limit"], 10)


class TestServer(unittest.TestCase):
    """Test the MCP server."""

    def setUp(self):
        self.server = Server("test-server")

        @self.server.tool()
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        @self.server.tool(name="custom_name", description="Custom tool")
        def my_func(x: str) -> str:
            return x.upper()

        @self.server.resource(uri="test://data")
        def get_data() -> str:
            """Get test data."""
            return "test data"

    def test_tool_registration(self):
        tools = self.server.list_tools()
        names = [t["name"] for t in tools]
        self.assertIn("add", names)
        self.assertIn("custom_name", names)

    def test_resource_registration(self):
        resources = self.server.list_resources()
        uris = [r["uri"] for r in resources]
        self.assertIn("test://data", uris)

    def test_tool_call(self):
        result = asyncio.run(self.server.call_tool("add", {"a": 3, "b": 4}))
        self.assertEqual(result[0]["type"], "text")
        self.assertIn("7", result[0]["text"])

    def test_tool_call_unknown(self):
        with self.assertRaises(KeyError):
            asyncio.run(self.server.call_tool("nonexistent", {}))

    def test_message_handler_initialize(self):
        message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        result = asyncio.run(self.server._handle_message(message))
        self.assertEqual(result["id"], 1)
        self.assertIn("serverInfo", result["result"])

    def test_message_handler_tools_list(self):
        message = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        result = asyncio.run(self.server._handle_message(message))
        self.assertIn("tools", result["result"])

    def test_message_handler_ping(self):
        message = {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}}
        result = asyncio.run(self.server._handle_message(message))
        self.assertEqual(result["result"], {})


if __name__ == "__main__":
    unittest.main()
