"""
Good Agent with ADK/A2A implementation
Legitimate email summarizer agent
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

class EmailSummarizerTool(Tool):
    """Tool for summarizing email content"""
    
    def name(self) -> str:
        return "email_summarizer"
    
    def description(self) -> str:
        return "Summarize email messages into concise insights"
    
    async def execute(self, params: Dict[str, Any]) -> Any:
        emails = params.get("emails", [])
        
        # Simple summarization logic
        message_count = len(emails.get("messages", []))
        
        if message_count == 0:
            return "No emails to summarize."
        elif message_count < 5:
            return f"You have {message_count} recent emails. Looks like a quiet inbox!"
        elif message_count < 10:
            return f"You have {message_count} emails. Normal activity level."
        else:
            return f"You have {message_count} emails. Busy inbox - might want to catch up!"

class GoodAgent(BaseAgent):
    """Good Agent - legitimate email summarizer"""
    
    def __init__(self):
        # Create agent card
        agent_card = AgentCard(
            agent_id="good_agent",
            name="Email Summarizer Pro",
            description="Professional email summarization service",
            version="1.0.0",
            capabilities=[
                "email_summarization",
                "inbox_insights",
                "activity_analysis"
            ],
            tools=["email_summarizer"],
            endpoints={
                "execute": "http://good_agent:8003/execute_task",
                "status": "http://good_agent:8003/status"
            },
            metadata={
                "trust_level": 3,
                "category": "productivity",
                "verified": True
            }
        )
        
        super().__init__(agent_card)
        
        # Register tools
        self.summarizer_tool = EmailSummarizerTool()
        self.register_tool(self.summarizer_tool)
        
        # A2A client for communicating with Personal Agent
        self.a2a_client = A2AClient("good_agent")
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email summarization tasks"""
        
        task_type = task.get("type", "summarize_emails")
        
        if task_type == "summarize_emails":
            return await self._summarize_emails(task)
        elif task_type == "analyze_activity":
            return await self._analyze_activity(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _summarize_emails(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize user's emails"""
        
        user_id = task.get("user_id")
        
        # Request email data from Personal Agent
        personal_agent_url = os.environ.get("PERSONAL_AGENT_URL", "http://personal_agent:8002")
        
        try:
            # Use A2A to request Gmail read through Personal Agent
            email_data = await self.a2a_client.execute_task(
                agent_url=personal_agent_url,
                recipient_id="personal_agent",
                task={
                    "type": "proxy_gmail_read",
                    "user_id": user_id,
                    "agent_id": "good_agent"
                }
            )
            
            # Extract email data from response
            if "data" in email_data:
                emails = email_data["data"]
            else:
                emails = email_data
            
            # Summarize emails
            summary = await self.use_tool("email_summarizer", {"emails": emails})
            
            # Store summary in session
            self.memorize(f"summary_{user_id}", summary)
            self.session_state.add_to_history({
                "action": "email_summarized",
                "user_id": user_id,
                "summary": summary
            })
            
            return {
                "status": "success",
                "summary": summary,
                "agent": "good_agent",
                "message": "Email summary generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to summarize emails: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": "good_agent",
                "message": "Failed to access or summarize emails"
            }
    
    async def _analyze_activity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email activity patterns"""
        
        user_id = task.get("user_id")
        
        # Get previously stored summary
        previous_summary = self.recall(f"summary_{user_id}")
        
        if previous_summary:
            analysis = f"Based on recent activity: {previous_summary}"
        else:
            # Get fresh data
            result = await self._summarize_emails(task)
            analysis = result.get("summary", "No activity data available")
        
        return {
            "status": "success",
            "analysis": analysis,
            "agent": "good_agent"
        }