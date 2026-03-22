"""Transport layers for MCP communication (stdio and SSE)."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Callable, Awaitable


class StdioTransport:
    """Communicate over stdin/stdout using JSON-RPC messages.

    This is the standard transport for MCP servers that integrate
    with tools like Claude Desktop, Cursor, and similar clients.
    """

    def __init__(self, handler: Callable[[dict], Awaitable[dict]]):
        self.handler = handler

    async def run(self) -> None:
        """Start the stdio event loop, reading JSON-RPC from stdin."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(
            lambda: protocol, sys.stdin.buffer
        )

        while True:
            line = await reader.readline()
            if not line:
                break

            try:
                message = json.loads(line.decode().strip())
                response = await self.handler(message)
                if response is not None:
                    output = json.dumps(response) + "\n"
                    sys.stdout.write(output)
                    sys.stdout.flush()
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


class SSETransport:
    """Communicate over HTTP using Server-Sent Events.

    Useful for web-based MCP clients that connect over HTTP.
    """

    def __init__(self, handler: Callable[[dict], Awaitable[dict]], port: int = 8080):
        self.handler = handler
        self.port = port

    async def run(self) -> None:
        """Start the SSE HTTP server."""
        try:
            from aiohttp import web
        except ImportError:
            raise ImportError(
                "aiohttp is required for SSE transport. "
                "Install it with: pip install aiohttp"
            )

        app = web.Application()
        app.router.add_post("/message", self._handle_post)
        app.router.add_get("/sse", self._handle_sse)
        app.router.add_get("/health", self._handle_health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        print(f"MCP SSE server running on http://0.0.0.0:{self.port}")
        await site.start()

        # Keep running
        await asyncio.Event().wait()

    async def _handle_post(self, request: Any) -> Any:
        from aiohttp import web

        body = await request.json()
        response = await self.handler(body)
        return web.json_response(response)

    async def _handle_sse(self, request: Any) -> Any:
        from aiohttp import web

        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        endpoint_data = json.dumps({"endpoint": "/message"})
        await response.write(f"event: endpoint\ndata: {endpoint_data}\n\n".encode())

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(30)
                await response.write(b": keepalive\n\n")
        except (ConnectionResetError, asyncio.CancelledError):
            pass

        return response

    async def _handle_health(self, request: Any) -> Any:
        from aiohttp import web
        return web.json_response({"status": "ok"})
