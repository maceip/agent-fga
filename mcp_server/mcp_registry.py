"""
MCP (Marketplace) Registry Server
Acts as a centralized registry for Task Agents
"""

from fastapi import FastAPI, HTTPException, Request
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MCPRegistry:
    """Registry for agent discovery and management"""
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_endpoints: Dict[str, str] = {}
        
    def register_agent(self, agent_card: Dict[str, Any], endpoint: str):
        """Register an agent with the registry"""
        agent_id = agent_card["agent_id"]
        self.agents[agent_id] = {
            **agent_card,
            "registered_at": datetime.utcnow().isoformat(),
            "endpoint": endpoint
        }
        self.agent_endpoints[agent_id] = endpoint
        logger.info(f"Registered agent: {agent_id} at {endpoint}")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_endpoints[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return list(self.agents.values())
    
    def find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find agents with a specific capability"""
        matching_agents = []
        for agent in self.agents.values():
            if capability in agent.get("capabilities", []):
                matching_agents.append(agent)
        return matching_agents
    
    def find_agents_by_tool(self, tool: str) -> List[Dict[str, Any]]:
        """Find agents with a specific tool"""
        matching_agents = []
        for agent in self.agents.values():
            if tool in agent.get("tools", []):
                matching_agents.append(agent)
        return matching_agents

class MCPServer:
    """MCP Server for agent marketplace"""
    
    def __init__(self, port: int = 8090):
        self.registry = MCPRegistry()
        self.port = port
        self.app = FastAPI(title="MCP Marketplace Server")
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/register")
        async def register_agent(request: Request):
            """Register a new agent"""
            data = await request.json()
            agent_card = data.get("agent_card")
            endpoint = data.get("endpoint")
            
            if not agent_card or not endpoint:
                raise HTTPException(status_code=400, detail="Missing agent_card or endpoint")
            
            self.registry.register_agent(agent_card, endpoint)
            return {"status": "registered", "agent_id": agent_card["agent_id"]}
        
        @self.app.delete("/unregister/{agent_id}")
        async def unregister_agent(agent_id: str):
            """Unregister an agent"""
            self.registry.unregister_agent(agent_id)
            return {"status": "unregistered", "agent_id": agent_id}
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents"""
            return {"agents": self.registry.list_agents()}
        
        @self.app.get("/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """Get specific agent"""
            agent = self.registry.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            return agent
        
        @self.app.get("/discover/capability/{capability}")
        async def discover_by_capability(capability: str):
            """Discover agents by capability"""
            agents = self.registry.find_agents_by_capability(capability)
            return {"capability": capability, "agents": agents}
        
        @self.app.get("/discover/tool/{tool}")
        async def discover_by_tool(tool: str):
            """Discover agents by tool"""
            agents = self.registry.find_agents_by_tool(tool)
            return {"tool": tool, "agents": agents}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "registered_agents": len(self.registry.agents),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run(self):
        """Run the MCP server"""
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)