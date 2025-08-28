"""
A2A Client for agent-to-agent communication
"""

import httpx
from typing import Dict, Any, Optional
import json
import logging

from .a2a_server import A2AMessage

logger = logging.getLogger(__name__)

class A2AClient:
    """Client for communicating with A2A agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.client = httpx.AsyncClient()
        
    async def discover_agent(self, agent_url: str) -> Dict[str, Any]:
        """Discover an agent by retrieving its card"""
        try:
            response = await self.client.get(f"{agent_url}/agent_card")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to discover agent at {agent_url}: {str(e)}")
            raise
    
    async def execute_task(self, 
                          agent_url: str,
                          recipient_id: str,
                          task: Dict[str, Any],
                          correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task on a remote agent"""
        
        # Create A2A message
        message = A2AMessage(
            message_type="execute_task",
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            payload=task,
            correlation_id=correlation_id
        )
        
        try:
            response = await self.client.post(
                f"{agent_url}/execute_task",
                json=message.to_dict()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to execute task on {agent_url}: {str(e)}")
            raise
    
    async def query_capabilities(self, agent_url: str) -> Dict[str, Any]:
        """Query agent capabilities"""
        try:
            response = await self.client.get(f"{agent_url}/capabilities")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to query capabilities from {agent_url}: {str(e)}")
            raise
    
    async def query_tool(self, agent_url: str, tool_name: str) -> bool:
        """Check if agent has a specific tool"""
        try:
            response = await self.client.post(
                f"{agent_url}/query_tool",
                json={"tool_name": tool_name}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("has_tool", False)
        except Exception as e:
            logger.error(f"Failed to query tool from {agent_url}: {str(e)}")
            return False
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()