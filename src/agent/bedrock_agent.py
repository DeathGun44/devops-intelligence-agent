"""
AWS Bedrock Agent Implementation with Reasoning Capabilities
"""
import json
import logging
from typing import Dict, Any, List, Optional
import boto3
from datetime import datetime

from src.config import settings
from src.agent.tools import ToolRegistry
from src.agent.reasoning import ReasoningEngine
# Use DynamoDB for persistent storage (infrastructure is now deployed)
from src.storage.dynamodb import ConversationStore


logger = logging.getLogger(__name__)


class DevOpsAgent:
    """
    Main DevOps Intelligence Agent using AWS Bedrock
    with autonomous reasoning and multi-tool capabilities
    """
    
    def __init__(self):
        self.bedrock_runtime = None
        self.bedrock_agent = None
        self.tool_registry = None
        self.reasoning_engine = None
        self.conversation_store = None
        
    async def initialize(self):
        """Initialize AWS clients and agent components"""
        try:
            # Initialize AWS clients
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_REGION
            )
            
            self.bedrock_agent = boto3.client(
                'bedrock-agent-runtime',
                region_name=settings.AWS_REGION
            )
            
            # Initialize tool registry
            self.tool_registry = ToolRegistry()
            await self.tool_registry.initialize()
            
            # Initialize reasoning engine
            self.reasoning_engine = ReasoningEngine(
                bedrock_client=self.bedrock_runtime,
                model_id=settings.BEDROCK_MODEL_ID
            )
            
            # Initialize conversation store
            self.conversation_store = ConversationStore()
            await self.conversation_store.initialize()
            
            logger.info("DevOps Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with autonomous reasoning
        
        Args:
            message: User input message
            session_id: Unique session identifier
            context: Optional context information
            
        Returns:
            Agent response with actions taken
        """
        try:
            # Retrieve conversation history
            history = await self.conversation_store.get_history(session_id)
            
            # Store user message
            await self.conversation_store.add_message(
                session_id=session_id,
                role="user",
                content=message
            )
            
            # Reasoning phase: Analyze the request and plan actions
            reasoning_result = await self.reasoning_engine.reason(
                query=message,
                history=history,
                available_tools=self.tool_registry.get_tool_definitions(),
                context=context
            )
            
            logger.info(f"Reasoning completed: {reasoning_result['plan']}")
            
            # Execution phase: Execute planned actions
            execution_results = await self._execute_plan(
                plan=reasoning_result['plan'],
                session_id=session_id
            )
            
            # Generate final response
            final_response = await self._generate_response(
                reasoning=reasoning_result,
                execution_results=execution_results,
                history=history
            )
            
            # Store agent response
            await self.conversation_store.add_message(
                session_id=session_id,
                role="assistant",
                content=final_response['message']
            )
            
            return {
                "message": final_response['message'],
                "reasoning": reasoning_result['reasoning'],
                "actions_taken": execution_results,
                "requires_approval": final_response.get('requires_approval', False),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "message": "I encountered an error processing your request. Please try again.",
                "error": str(e),
                "session_id": session_id
            }
    
    async def _execute_plan(
        self,
        plan: List[Dict[str, Any]],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Execute the planned actions"""
        results = []
        
        for step in plan:
            tool_name = step.get('tool')
            tool_input = step.get('input', {})
            
            try:
                # Check if human approval is required
                if step.get('requires_approval') and settings.ENABLE_HUMAN_APPROVAL:
                    # Store pending action for approval
                    await self._store_pending_action(session_id, step)
                    results.append({
                        "tool": tool_name,
                        "status": "pending_approval",
                        "message": "Action requires human approval"
                    })
                    continue
                
                # Execute the tool
                tool_result = await self.tool_registry.execute_tool(
                    tool_name=tool_name,
                    tool_input=tool_input
                )
                
                results.append({
                    "tool": tool_name,
                    "status": "success",
                    "result": tool_result
                })
                
                logger.info(f"Executed tool {tool_name}: {tool_result.get('message', 'Success')}")
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                results.append({
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    async def _generate_response(
        self,
        reasoning: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate final response using LLM"""
        
        # Prepare context for response generation
        context = {
            "reasoning": reasoning['reasoning'],
            "plan": reasoning['plan'],
            "execution_results": execution_results
        }
        
        # Create prompt for response generation
        prompt = f"""You are a DevOps Intelligence Agent. Based on the following information, 
generate a clear, helpful response to the user.

Reasoning: {reasoning['reasoning']}

Actions Taken:
{json.dumps(execution_results, indent=2)}

Provide a natural, conversational response that:
1. Summarizes what you understood about their request
2. Explains what actions you took or plan to take
3. Provides any relevant insights or recommendations
4. If actions are pending approval, clearly state this

Response:"""

        try:
            # Prepare request body based on model type
            if "anthropic" in settings.BEDROCK_MODEL_ID.lower():
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                }
            else:
                # Amazon Nova format
                request_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 2000,
                        "temperature": 0.7
                    }
                }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=settings.BEDROCK_MODEL_ID,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Parse response based on model type
            if "anthropic" in settings.BEDROCK_MODEL_ID.lower():
                message = response_body['content'][0]['text']
            else:
                message = response_body['output']['message']['content'][0]['text']
            
            # Check if any actions require approval
            requires_approval = any(
                r.get('status') == 'pending_approval' 
                for r in execution_results
            )
            
            return {
                "message": message,
                "requires_approval": requires_approval
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "message": "I've processed your request. Please check the action results for details.",
                "requires_approval": False
            }
    
    async def _store_pending_action(self, session_id: str, action: Dict[str, Any]):
        """Store action pending approval in DynamoDB"""
        dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        table = dynamodb.Table(settings.DYNAMODB_ACTIONS_TABLE)
        
        table.put_item(
            Item={
                'session_id': session_id,
                'action_id': f"{session_id}-{datetime.utcnow().timestamp()}",
                'action': json.dumps(action),
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
        )
    
    async def approve_action(self, session_id: str, action_id: str) -> Dict[str, Any]:
        """Approve and execute a pending action"""
        # Retrieve action from DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        table = dynamodb.Table(settings.DYNAMODB_ACTIONS_TABLE)
        
        response = table.get_item(
            Key={'session_id': session_id, 'action_id': action_id}
        )
        
        if 'Item' not in response:
            return {"error": "Action not found"}
        
        action = json.loads(response['Item']['action'])
        
        # Execute the action
        result = await self.tool_registry.execute_tool(
            tool_name=action['tool'],
            tool_input=action['input']
        )
        
        # Update action status
        table.update_item(
            Key={'session_id': session_id, 'action_id': action_id},
            UpdateExpression='SET #status = :status, executed_at = :executed_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'executed',
                ':executed_at': datetime.utcnow().isoformat()
            }
        )
        
        return result
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up agent resources...")
        if self.tool_registry:
            await self.tool_registry.cleanup()

