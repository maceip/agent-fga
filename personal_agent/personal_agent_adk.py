"""
Personal Agent with ADK/A2A implementation
User's trusted agent that manages permissions and proxies Gmail API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
import httpx
import logging

from adk_core.base_agent import BaseAgent, AgentCard, Tool
from a2a_core.a2a_client import A2AClient

logger = logging.getLogger(__name__)

class GmailReadTool(Tool):
    """Tool for reading Gmail messages"""
    
    def __init__(self, token_storage: Dict[str, str]):
        self.token_storage = token_storage
        
    def name(self) -> str:
        return "gmail_read"
    
    def description(self) -> str:
        return "Read emails from user's Gmail account"
    
    async def execute(self, params: Dict[str, Any]) -> Any:
        user_id = params.get("user_id")
        access_token = self.token_storage.get(user_id)
        
        if not access_token:
            raise ValueError("No access token available for user")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=3",
                headers=headers
            )
            res.raise_for_status()
            return res.json()

class OpenFGATool(Tool):
    """Tool for managing OpenFGA permissions"""
    
    def __init__(self, openfga_url: str, store_id: str):
        self.openfga_url = openfga_url
        self.store_id = store_id
        
    def name(self) -> str:
        return "openfga_manage"
    
    def description(self) -> str:
        return "Manage fine-grained permissions with OpenFGA"
    
    async def execute(self, params: Dict[str, Any]) -> Any:
        action = params.get("action")  # "grant" or "revoke"
        user = params.get("user")
        relation = params.get("relation")
        object_id = params.get("object")
        
        async with httpx.AsyncClient() as client:
            if action == "grant":
                await client.post(
                    f"{self.openfga_url}/stores/{self.store_id}/write",
                    json={
                        "writes": {
                            "tuple_keys": [{
                                "user": user,
                                "relation": relation,
                                "object": object_id
                            }]
                        }
                    }
                )
                return {"status": "granted"}
            elif action == "revoke":
                await client.post(
                    f"{self.openfga_url}/stores/{self.store_id}/write",
                    json={
                        "deletes": {
                            "tuple_keys": [{
                                "user": user,
                                "relation": relation,
                                "object": object_id
                            }]
                        }
                    }
                )
                return {"status": "revoked"}
            elif action == "check":
                res = await client.post(
                    f"{self.openfga_url}/stores/{self.store_id}/check",
                    json={
                        "tuple_key": {
                            "user": user,
                            "relation": relation,
                            "object": object_id
                        }
                    }
                )
                return res.json()
        
        return {"status": "unknown_action"}

class PersonalAgent(BaseAgent):
    """Personal Agent - user's trusted agent managing Gmail access"""
    
    def __init__(self):
        # Create agent card
        agent_card = AgentCard(
            agent_id="personal_agent",
            name="Personal Gmail Agent",
            description="User's trusted agent that manages Gmail permissions and access",
            version="1.0.0",
            capabilities=[
                "gmail_management",
                "permission_control",
                "secure_delegation"
            ],
            tools=["gmail_read", "openfga_manage"],
            endpoints={
                "execute": "http://personal_agent:8002/execute_task",
                "status": "http://personal_agent:8002/status"
            },
            metadata={
                "trust_level": 5,
                "owner": "user"
            }
        )
        
        super().__init__(agent_card)
        
        # Initialize tools
        self.token_storage = {}
        self.gmail_tool = GmailReadTool(self.token_storage)
        self.openfga_tool = OpenFGATool(
            os.environ.get("OPENFGA_API_URL", "http://openfga:8080"),
            os.environ.get("OPENFGA_STORE_ID", "")
        )
        
        # Register tools
        self.register_tool(self.gmail_tool)
        self.register_tool(self.openfga_tool)
        
        # A2A client for communicating with other agents
        self.a2a_client = A2AClient("personal_agent")
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks related to Gmail management and delegation"""
        
        task_type = task.get("type")
        
        if task_type == "delegate_access":
            return await self._delegate_access(task)
        elif task_type == "revoke_access":
            return await self._revoke_access(task)
        elif task_type == "check_permission":
            return await self._check_permission(task)
        elif task_type == "proxy_gmail_read":
            return await self._proxy_gmail_read(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _delegate_access(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate temporary access to another agent"""
        
        user_id = task.get("user_id")
        agent_id = task.get("agent_id")
        access_token = task.get("access_token")
        agent_url = task.get("agent_url")
        
        # Store access token
        self.token_storage[user_id] = access_token
        self.memorize(f"token_{user_id}", access_token)
        
        # Grant permission in OpenFGA
        await self.use_tool("openfga_manage", {
            "action": "grant",
            "user": f"agent:{agent_id}",
            "relation": "temporary_reader",
            "object": f"gmail_account:{user_id}"
        })
        
        try:
            # Execute task on delegated agent via A2A
            if agent_url:
                result = await self.a2a_client.execute_task(
                    agent_url=agent_url,
                    recipient_id=agent_id,
                    task={
                        "type": "summarize_emails",
                        "user_id": user_id
                    }
                )
                return result
            else:
                return {"status": "delegated", "agent_id": agent_id}
        finally:
            # Always revoke permission after task
            await self.use_tool("openfga_manage", {
                "action": "revoke",
                "user": f"agent:{agent_id}",
                "relation": "temporary_reader",
                "object": f"gmail_account:{user_id}"
            })
            
            # Clear token
            self.token_storage.pop(user_id, None)
    
    async def _revoke_access(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Revoke access from an agent"""
        
        user_id = task.get("user_id")
        agent_id = task.get("agent_id")
        
        result = await self.use_tool("openfga_manage", {
            "action": "revoke",
            "user": f"agent:{agent_id}",
            "relation": "temporary_reader",
            "object": f"gmail_account:{user_id}"
        })
        
        return {"status": "revoked", "agent_id": agent_id}
    
    async def _check_permission(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an agent has permission"""
        
        user_id = task.get("user_id")
        agent_id = task.get("agent_id")
        relation = task.get("relation", "can_read_emails")
        
        result = await self.use_tool("openfga_manage", {
            "action": "check",
            "user": f"agent:{agent_id}",
            "relation": relation,
            "object": f"gmail_account:{user_id}"
        })
        
        return result
    
    async def _proxy_gmail_read(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy Gmail read request after permission check"""
        
        user_id = task.get("user_id")
        agent_id = task.get("agent_id")
        
        # Check permission
        perm_check = await self._check_permission({
            "user_id": user_id,
            "agent_id": agent_id,
            "relation": "can_read_emails"
        })
        
        if not perm_check.get("allowed", False):
            raise PermissionError(f"Agent {agent_id} not allowed to read emails")
        
        # Read emails
        emails = await self.use_tool("gmail_read", {"user_id": user_id})
        
        # Log access
        self.session_state.add_to_history({
            "action": "gmail_read",
            "agent_id": agent_id,
            "user_id": user_id,
            "email_count": len(emails.get("messages", []))
        })
        
        return emails