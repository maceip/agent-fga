"""
MCP Server main entry point
"""

from mcp_registry import MCPServer
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    server = MCPServer(port=8090)
    server.run()