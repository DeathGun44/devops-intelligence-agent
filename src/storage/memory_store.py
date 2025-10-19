"""
In-memory storage (for testing without DynamoDB)
"""
import logging
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryConversationStore:
    """Store conversations in memory instead of DynamoDB"""
    
    def __init__(self):
        self.conversations = defaultdict(list)
        self.sessions = {}
    
    async def initialize(self):
        """Initialize memory store"""
        logger.info("Using in-memory conversation store (no DynamoDB)")
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """Add a message to conversation history"""
        from datetime import datetime
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversations[session_id].append(message)
        self.sessions[session_id] = {
            'last_activity': message['timestamp'],
            'message_count': len(self.conversations[session_id])
        }
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history"""
        messages = self.conversations.get(session_id, [])
        return messages[-limit:] if messages else []

