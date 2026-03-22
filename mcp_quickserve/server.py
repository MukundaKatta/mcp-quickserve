"""Core MCP server with decorator-based tool and resource registration."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Callable

from .schema import generate_schema
from .validation import validate_input, ValidationError
from .transport import StdioTransport, SSETransport


class ToolDefinition:
    """Holds metadata for a registered MCP tool."""

    def __init__(self, func: Callable, name: str, description: str):
        self.func = func
        self.name = name
        self.description = description
        self.schema = generate_schema(func)


class ResourceDefinition:
    """Holds metadata for a registered MCP resource."""

    def __init__(self, func: Callable, uri: str, name: str, description: str):
        self.func = func
        self.uri = uri
        self.name = name
        self.description = description


class Server:
    """A minimal MCP server that registers tools and resources via decorators.

    Usage:
        server = Server("my-server")

        @server.tool()
        def greet(name: str) -> str:
            \"\"\"Greet someone by name.\"\"\"
            return f"Hello, {name}!"

        server.run()
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: dict[str, ToolDefinition] = {}
        self._resources: dict[str, ResourceDefinition] = {}

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable:
        """Decorator to register a function as an MCP tool.

        Args:
            name: Override the tool name (defaults to function name).
            description: Override the description (defaults to docstring).
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or (func.__doc__ or "").strip().split("\n")[0]
            self._tools[tool_name] = ToolDefinition(func, tool_name, tool_desc)
            return func
        return decorator

    def resource(
        self,
        uri: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable:
        """Decorator to register a function as an MCP resource.

        Args:
            uri: The resource URI (e.g., "file:///logs/app.log").
            name: Override the resource name.
            description: Override the description.
        """
        def decorator(func: Callable) -> Callable:
            res_name = name or func.__name__
            res_desc = description or (func.__doc__ or "").strip().split("\n")[0]
            self._resources[uri] = ResourceDefinition(func, uri, res_name, res_desc)
            return func
        return decorator

    def list_tools(self) -> list[dict[str, Any]]:
        """Return the tool listing in MCP format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.schema,
            }
            for t in self._tools.values()
        ]

    def list_resources(self) -> list[dict[str, Any]]:
        """Return the resource listing in MCP format."""
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
            }
            for r in self._resources.values()
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke a registered tool by name with the given arguments.

        Args:
            name: The tool name.
            arguments: The input arguments.

        Returns:
            The tool result wrapped in MCP content format.

        Raises:
            KeyError: If the tool is not registered.
            ValidationError: If input validation fails.
        """
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")

        tool = self._tools[name]
        validated = validate_input(arguments, tool.schema)

        if inspect.iscoroutinefunction(tool.func):
            result = await tool.func(**validated)
        else:
            result = tool.func(**validated)

        # Wrap in MCP content format
        if isinstance(result, str):
            return [{"type": "text", "text": result}]
        else:
            return [{"type": "text", "text": json.dumps(result, default=str)}]

    async def _handle_message(self, message: dict) -> dict | None:
        """Handle an incoming JSON-RPC message."""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        try:
            if method == "initialize":
                return self._response(msg_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version,
                    },
                })

            elif method == "notifications/initialized":
                return None

            elif method == "tools/list":
                return self._response(msg_id, {"tools": self.list_tools()})

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                content = await self.call_tool(tool_name, arguments)
                return self._response(msg_id, {"content": content})

            elif method == "resources/list":
                return self._response(msg_id, {"resources": self.list_resources()})

            elif method == "resources/read":
                uri = params.get("uri", "")
                return await self._handle_resource_read(msg_id, uri)

            elif method == "ping":
                return self._response(msg_id, {})

            else:
                return self._error(msg_id, -32601, f"Method not found: {method}")

        except ValidationError as e:
            return self._error(msg_id, -32602, str(e))
        except KeyError as e:
            return self._error(msg_id, -32602, str(e))
        except Exception as e:
            return self._error(msg_id, -32603, f"Internal error: {e}")

    async def _handle_resource_read(self, msg_id: Any, uri: str) -> dict:
        """Handle a resource read request."""
        if uri not in self._resources:
            return self._error(msg_id, -32602, f"Unknown resource: {uri}")

        resource = self._resources[uri]
        if inspect.iscoroutinefunction(resource.func):
            content = await resource.func()
        else:
            content = resource.func()

        return self._response(msg_id, {
            "contents": [
                {
                    "uri": uri,
                    "text": str(content),
                    "mimeType": "text/plain",
                }
            ]
        })

    @staticmethod
    def _response(msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    def run(self, transport: str = "stdio", port: int = 8080) -> None:
        """Start the MCP server.

        Args:
            transport: Either "stdio" or "sse".
            port: Port for SSE transport (default 8080).
        """
        if transport == "stdio":
            t = StdioTransport(self._handle_message)
        elif transport == "sse":
            t = SSETransport(self._handle_message, port=port)
        else:
            raise ValueError(f"Unknown transport: {transport}. Use 'stdio' or 'sse'.")

        asyncio.run(t.run())
