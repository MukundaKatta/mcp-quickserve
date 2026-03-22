"""Interactive demo showcasing mcp-quickserve features.

This script creates a server and tests tool calls locally
without needing an MCP client connection.

Run with:
    python examples/demo.py
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_quickserve import Server


# Create server
server = Server("demo-server", version="0.1.0")


@server.tool()
def greet(name: str, enthusiasm: int = 1) -> str:
    """Greet someone with configurable enthusiasm."""
    return f"Hello, {name}{'!' * enthusiasm}"


@server.tool(name="word_count", description="Count words in a text string")
def count_words(text: str) -> dict:
    """Count words and characters in text."""
    words = text.split()
    return {
        "words": len(words),
        "characters": len(text),
        "unique_words": len(set(w.lower() for w in words)),
    }


@server.tool()
def fibonacci(n: int) -> list[int]:
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq


@server.resource(uri="info://server/version")
def server_version() -> str:
    """Return the server version string."""
    return f"{server.name} v{server.version}"


async def run_demo():
    """Run the interactive demo."""
    print("=" * 60)
    print("  mcp-quickserve Demo")
    print("=" * 60)

    # Show registered tools
    print("\nRegistered tools:")
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")
        print(f"    Schema: {json.dumps(tool['inputSchema'], indent=6)}")

    # Show registered resources
    print("\nRegistered resources:")
    for resource in server.list_resources():
        print(f"  - {resource['uri']}: {resource['description']}")

    # Test tool calls
    print("\n" + "-" * 60)
    print("Testing tool calls:")
    print("-" * 60)

    # Test greet
    result = await server.call_tool("greet", {"name": "World", "enthusiasm": 3})
    print(f"\ngreet(name='World', enthusiasm=3):")
    print(f"  Result: {result}")

    # Test word_count
    result = await server.call_tool("word_count", {
        "text": "The quick brown fox jumps over the lazy dog"
    })
    print(f"\nword_count(text='The quick brown fox...'):")
    print(f"  Result: {result}")

    # Test fibonacci
    result = await server.call_tool("fibonacci", {"n": 10})
    print(f"\nfibonacci(n=10):")
    print(f"  Result: {result}")

    # Test default parameters
    result = await server.call_tool("greet", {"name": "Developer"})
    print(f"\ngreet(name='Developer') [default enthusiasm]:")
    print(f"  Result: {result}")

    # Test validation error
    print(f"\nTesting validation (missing required field):")
    try:
        await server.call_tool("greet", {})
    except Exception as e:
        print(f"  Caught expected error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(run_demo())
