"""
A2A Server implementation for agent-to-agent communication
Based on a2a-samples patterns
"""

from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from adk_core.base_agent import BaseAgent, AgentCard
from adk_core.agent_executor import AgentExecutor

logger = logging.getLogger(__name__)

class A2AMessage:
    """Standard A2A message format"""
    def __init__(self, 
                 message_type: str,
                 sender_id: str,
                 recipient_id: str,
                 payload: Dict[str, Any],
                 correlation_id: Optional[str] = None):
        self.message_type = message_type
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.payload = payload
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_type": self.message_type,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        return cls(
            message_type=data["message_type"],
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            payload=data["payload"],
            correlation_id=data.get("correlation_id")
        )

class A2AServer:
    """A2A Server hosting an agent"""
    
    def __init__(self, agent: BaseAgent, port: int = 8000):
        self.agent = agent
        self.executor = AgentExecutor(agent)
        self.port = port
        self.app = FastAPI(title=f"A2A Server - {agent.agent_card.name}")
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes for A2A communication"""
        
        @self.app.get("/agent_card")
        async def get_agent_card():
            """Return the agent's card for discovery"""
            return json.loads(self.agent.agent_card.to_json())
        
        @self.app.post("/execute_task")
        async def execute_task(request: Request):
            """Execute a task sent via A2A protocol"""
            data = await request.json()
            
            # Parse A2A message
            try:
                message = A2AMessage.from_dict(data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid A2A message: {str(e)}")
            
            # Verify this agent is the recipient
            if message.recipient_id != self.agent.agent_card.agent_id:
                raise HTTPException(status_code=400, detail="Message not intended for this agent")
            
            # Execute the task
            result = await self.executor.execute(message.payload)
            
            # Create response message
            response = A2AMessage(
                message_type="task_response",
                sender_id=self.agent.agent_card.agent_id,
                recipient_id=message.sender_id,
                payload=result.to_dict(),
                correlation_id=message.correlation_id
            )
            
            return response.to_dict()
        
        @self.app.get("/status")
        async def get_status():
            """Get agent status"""
            return self.executor.get_status()
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Get agent capabilities"""
            return {
                "agent_id": self.agent.agent_card.agent_id,
                "capabilities": self.agent.agent_card.capabilities,
                "tools": self.agent.agent_card.tools
            }
        
        @self.app.post("/query_tool")
        async def query_tool(request: Request):
            """Query if agent has a specific tool"""
            data = await request.json()
            tool_name = data.get("tool_name")
            
            has_tool = tool_name in self.agent.agent_card.tools
            return {"has_tool": has_tool, "tool_name": tool_name}
    
    def run(self):
        """Run the A2A server"""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)