# mcp-quickserve

Build MCP (Model Context Protocol) servers in minutes with Python decorators. No boilerplate, no config files - just define your tools and go.

## What is MCP?

MCP is an open standard for connecting AI models to external tools and data sources. Think of it as the USB-C of AI tooling - one protocol that works with any LLM client (Claude, GPT, local models, etc).

## Features

- Decorator-based tool and resource registration
- Automatic JSON Schema generation from Python type hints
- Built-in input validation with clear error messages
- Stdio and SSE transport layers
- Zero-config defaults with full customization options

## Quick Start

```python
from mcp_quickserve import Server

server = Server("my-server")

@server.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@server.tool()
def search(query: str, limit: int = 10) -> list[dict]:
    """Search for items matching the query."""
    return [{"title": f"Result for {query}", "rank": i} for i in range(limit)]

server.run()  # Starts stdio transport by default
```

## Installation

```bash
pip install -r requirements.txt
```

## Examples

Run the interactive demo to see all features in action:

```bash
python examples/demo.py
```

Other examples:

- `examples/calculator.py` - Basic arithmetic tools
- `examples/file_tools.py` - File operations with complex return types

## Architecture

```
mcp_quickserve/
  __init__.py      - Public API exports
  server.py        - Core server with decorator registration
  schema.py        - Type hint to JSON Schema conversion
  validation.py    - Input validation engine
  transport.py     - Stdio and SSE transport layers
```

## How It Works

1. Decorate Python functions with `@server.tool()` or `@server.resource()`
2. mcp-quickserve inspects type hints and docstrings to generate JSON Schema
3. When an MCP client sends a tool call, the server validates inputs against the schema
4. The function runs and results are returned in MCP-compliant format
5. All communication uses JSON-RPC 2.0 over stdio or SSE

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
