"""
DynamoDB storage for conversations and agent state
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

from src.config import settings

logger = logging.getLogger(__name__)


class ConversationStore:
    """Store and retrieve conversation history"""
    
    def __init__(self):
        self.dynamodb = None
        self.conversations_table = None
        self.sessions_table = None
    
    async def initialize(self):
        """Initialize DynamoDB connection"""
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        # Get or create tables
        self.conversations_table = await self._get_or_create_table(
            settings.DYNAMODB_CONVERSATIONS_TABLE,
            key_schema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            attribute_definitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ]
        )
        
        self.sessions_table = await self._get_or_create_table(
            settings.DYNAMODB_SESSIONS_TABLE,
            key_schema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'}
            ],
            attribute_definitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'}
            ]
        )
        
        logger.info("DynamoDB store initialized")
    
    async def _get_or_create_table(
        self,
        table_name: str,
        key_schema: List[Dict],
        attribute_definitions: List[Dict]
    ):
        """Get existing table or create if it doesn't exist"""
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            logger.info(f"Using existing table: {table_name}")
            return table
        except:
            logger.info(f"Creating table: {table_name}")
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            return table
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """Add a message to conversation history"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            self.conversations_table.put_item(
                Item={
                    'session_id': session_id,
                    'timestamp': timestamp,
                    'role': role,
                    'content': content,
                    'metadata': json.dumps(metadata or {})
                }
            )
            
            # Update session last activity
            self.sessions_table.put_item(
                Item={
                    'session_id': session_id,
                    'last_activity': timestamp,
                    'message_count': await self._get_message_count(session_id)
                }
            )
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history"""
        try:
            response = self.conversations_table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            messages = []
            for item in reversed(response['Items']):  # Reverse to get chronological order
                messages.append({
                    'role': item['role'],
                    'content': item['content'],
                    'timestamp': item['timestamp'],
                    'metadata': json.loads(item.get('metadata', '{}'))
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []
    
    async def _get_message_count(self, session_id: str) -> int:
        """Get message count for a session"""
        try:
            response = self.conversations_table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                Select='COUNT'
            )
            return response['Count']
        except:
            return 0

