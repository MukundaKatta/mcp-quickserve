"""Example: File operation tools as an MCP server.

Demonstrates tools with complex return types and optional parameters.

Run with:
    python examples/file_tools.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_quickserve import Server

server = Server("file-tools")


@server.tool()
def list_directory(path: str = ".") -> list[dict]:
    """List files and directories at the given path."""
    entries = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        stat = os.stat(full)
        entries.append({
            "name": name,
            "is_directory": os.path.isdir(full),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return sorted(entries, key=lambda e: e["name"])


@server.tool()
def read_file(path: str, max_lines: int = 100) -> str:
    """Read the contents of a text file, optionally limiting line count."""
    with open(path, "r") as f:
        lines = f.readlines()[:max_lines]
    return "".join(lines)


@server.tool()
def search_files(directory: str, pattern: str, max_results: int = 20) -> list[dict]:
    """Search for files whose names contain the given pattern."""
    results = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if pattern.lower() in fname.lower():
                full_path = os.path.join(root, fname)
                results.append({
                    "path": full_path,
                    "name": fname,
                    "size_bytes": os.path.getsize(full_path),
                })
                if len(results) >= max_results:
                    return results
    return results


@server.resource(uri="file:///cwd")
def get_cwd() -> str:
    """Return the current working directory."""
    return os.getcwd()


if __name__ == "__main__":
    print("File Tools MCP server ready.")
    print(f"Registered tools: {[t['name'] for t in server.list_tools()]}")
    print(f"Registered resources: {[r['uri'] for r in server.list_resources()]}")
    server.run()
