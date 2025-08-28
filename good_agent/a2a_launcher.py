"""
A2A Server launcher for Good Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from good_agent_adk import GoodAgent
from a2a_core.a2a_server import A2AServer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def register_with_mcp(agent_card, port):
    """Register agent with MCP server"""
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://mcp_server:8090")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_url}/register",
                json={
                    "agent_card": json.loads(agent_card.to_json()),
                    "endpoint": f"http://good_agent:{port}"
                }
            )
            response.raise_for_status()
            logger.info(f"Registered with MCP server: {response.json()}")
    except Exception as e:
        logger.warning(f"Failed to register with MCP: {str(e)}")

if __name__ == "__main__":
    import json
    
    # Create Good Agent
    agent = GoodAgent()
    
    # Create A2A server
    server = A2AServer(agent, port=8003)
    
    # Register with MCP
    asyncio.run(register_with_mcp(agent.agent_card, 8003))
    
    # Run server
    logger.info("Starting Good Agent A2A Server on port 8003")
    server.run()