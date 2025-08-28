"""
Agent Executor for managing agent state and task execution
Based on A2A samples patterns
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging

from .base_agent import BaseAgent, AgentCard

logger = logging.getLogger(__name__)

class TaskStatus:
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskResult:
    """Result of task execution"""
    def __init__(self, status: str, data: Any = None, error: str = None):
        self.status = status
        self.data = data
        self.error = error
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }

class AgentExecutor:
    """Manages agent lifecycle and task execution"""
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.current_task: Optional[Dict[str, Any]] = None
        self.task_status = TaskStatus.PENDING
        self.task_history: List[TaskResult] = []
        
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a task with the agent"""
        self.current_task = task
        self.task_status = TaskStatus.RUNNING
        
        try:
            # Initialize agent if needed
            await self.agent.initialize()
            
            # Log task start
            logger.info(f"Agent {self.agent.agent_card.agent_id} executing task: {task.get('type', 'unknown')}")
            
            # Execute the task
            result = await self.agent.execute_task(task)
            
            # Create success result
            task_result = TaskResult(
                status=TaskStatus.COMPLETED,
                data=result
            )
            
            self.task_status = TaskStatus.COMPLETED
            self.task_history.append(task_result)
            
            return task_result
            
        except Exception as e:
            # Create error result
            logger.error(f"Agent {self.agent.agent_card.agent_id} task failed: {str(e)}")
            
            task_result = TaskResult(
                status=TaskStatus.FAILED,
                error=str(e)
            )
            
            self.task_status = TaskStatus.FAILED
            self.task_history.append(task_result)
            
            return task_result
    
    async def execute_with_timeout(self, task: Dict[str, Any], timeout: int = 30) -> TaskResult:
        """Execute task with timeout"""
        try:
            return await asyncio.wait_for(
                self.execute(task),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Agent {self.agent.agent_card.agent_id} task timed out after {timeout} seconds")
            return TaskResult(
                status=TaskStatus.CANCELLED,
                error=f"Task timed out after {timeout} seconds"
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current executor status"""
        return {
            "agent_id": self.agent.agent_card.agent_id,
            "task_status": self.task_status,
            "current_task": self.current_task,
            "history_count": len(self.task_history)
        }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get task execution history"""
        return [result.to_dict() for result in self.task_history]