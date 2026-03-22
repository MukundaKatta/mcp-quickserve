"""mcp-quickserve - Minimal MCP server toolkit using decorators."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-quickserve",
    version="0.1.0",
    author="Mukunda Katta",
    description="Build MCP servers in minutes with Python decorators",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MukundaKatta/mcp-quickserve",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0",
        "aiohttp>=3.9",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
    ],
)
