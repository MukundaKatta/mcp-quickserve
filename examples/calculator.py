"""Example: A simple calculator MCP server.

Run with:
    python examples/calculator.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_quickserve import Server

server = Server("calculator")


@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@server.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@server.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@server.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    print("Calculator MCP server ready.")
    print(f"Registered tools: {[t['name'] for t in server.list_tools()]}")
    server.run()
