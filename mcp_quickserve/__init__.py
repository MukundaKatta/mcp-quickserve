"""mcp-quickserve: Minimal MCP server toolkit using decorators."""

from .server import Server
from .schema import generate_schema
from .validation import validate_input

__version__ = "0.1.0"
__all__ = ["Server", "generate_schema", "validate_input"]
