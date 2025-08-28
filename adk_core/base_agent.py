"""
Base ADK Agent following Google ADK patterns
Based on travel-concierge and expense reimbursement samples
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import json
import uuid
from datetime import datetime
from abc import ABC, abstractmethod

@dataclass
class AgentCard:
    """Agent Card defining agent identity and capabilities (A2A standard)"""
    agent_id: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    tools: List[str]
    endpoints: Dict[str, str]
    metadata: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "endpoints": self.endpoints,
            "metadata": self.metadata
        })

class SessionState:
    """Session state management for agent memory"""
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.data: Dict[str, Any] = {}
        self.conversation_history: List[Dict] = []
        self.created_at = datetime.utcnow()
        
    def memorize(self, key: str, value: Any):
        """Store information in session state"""
        self.data[key] = value
        
    def recall(self, key: str) -> Any:
        """Retrieve information from session state"""
        return self.data.get(key)
    
    def add_to_history(self, message: Dict):
        """Add message to conversation history"""
        self.conversation_history.append({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })

class Tool(ABC):
    """Base class for agent tools"""
    
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Any:
        pass

class BaseAgent(ABC):
    """Base ADK Agent class following Google patterns"""
    
    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card
        self.session_state = SessionState()
        self.tools: Dict[str, Tool] = {}
        self.sub_agents: Dict[str, 'BaseAgent'] = {}
        self._before_agent_callback: Optional[Callable] = None
        
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main task execution method - must be implemented by agents"""
        pass
    
    def register_tool(self, tool: Tool):
        """Register a tool for the agent to use"""
        self.tools[tool.name()] = tool
        
    def register_sub_agent(self, name: str, agent: 'BaseAgent'):
        """Register a sub-agent for delegation"""
        self.sub_agents[name] = agent
        
    async def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Use a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not registered")
        return await self.tools[tool_name].execute(params)
    
    async def transfer_to_agent(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer control to another agent"""
        if agent_name not in self.sub_agents:
            raise ValueError(f"Sub-agent {agent_name} not registered")
        
        # Share session state with sub-agent
        sub_agent = self.sub_agents[agent_name]
        sub_agent.session_state = self.session_state
        
        return await sub_agent.execute_task(task)
    
    def set_before_agent_callback(self, callback: Callable):
        """Set callback to load initial state"""
        self._before_agent_callback = callback
        
    async def initialize(self):
        """Initialize agent with any startup logic"""
        if self._before_agent_callback:
            await self._before_agent_callback(self.session_state)
    
    def get_agent_card(self) -> AgentCard:
        """Return the agent's card for discovery"""
        return self.agent_card
    
    def memorize(self, key: str, value: Any):
        """Store information in session memory"""
        self.session_state.memorize(key, value)
        
    def recall(self, key: str) -> Any:
        """Retrieve information from session memory"""
        return self.session_state.recall(key)