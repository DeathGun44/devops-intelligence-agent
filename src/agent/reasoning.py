"""
Reasoning Engine for Autonomous Decision Making
Uses AWS Bedrock LLM for complex reasoning and planning
"""
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Autonomous reasoning engine that analyzes requests,
    plans actions, and makes decisions
    """
    
    def __init__(self, bedrock_client, model_id: str):
        self.bedrock_client = bedrock_client
        self.model_id = model_id
    
    async def reason(
        self,
        query: str,
        history: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reason about the query and create an action plan
        
        Returns:
            reasoning: Explanation of the reasoning process
            plan: List of actions to take
        """
        
        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(
            query=query,
            history=history,
            available_tools=available_tools,
            context=context
        )
        
        try:
            # Prepare request body based on model type
            if "anthropic" in self.model_id.lower():
                # Anthropic Claude format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "system": self._get_system_prompt()
                }
            else:
                # Amazon Nova or other models format
                request_body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 4000,
                        "temperature": 0.3
                    },
                    "system": [{"text": self._get_system_prompt()}]
                }
            
            # Call Bedrock for reasoning
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Parse response based on model type
            if "anthropic" in self.model_id.lower():
                reasoning_text = response_body['content'][0]['text']
            else:
                # Amazon Nova format
                reasoning_text = response_body['output']['message']['content'][0]['text']
            
            # Parse the reasoning output
            parsed_result = self._parse_reasoning_output(reasoning_text)
            
            logger.info(f"Reasoning completed: {parsed_result['reasoning']}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error during reasoning: {e}", exc_info=True)
            return {
                "reasoning": "Unable to complete reasoning due to an error",
                "plan": []
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the reasoning agent"""
        return """You are an expert DevOps Intelligence Agent with deep knowledge of:
- Cloud infrastructure (AWS, Azure, GCP)
- CI/CD pipelines and deployment strategies
- Code analysis and security best practices
- Performance optimization and cost management
- Troubleshooting and incident response

CRITICAL RULES:
1. You MUST use the available tools to answer questions - DO NOT just provide instructions
2. When asked about AWS resources (EC2, Lambda, S3, etc.), USE the aws_infrastructure tool
3. When asked about costs, USE the cost_analysis tool
4. When asked to review code, USE the code_analysis tool
5. DO NOT tell users to use AWS CLI - you have direct access via tools

Your role is to:
1. Analyze user requests carefully
2. Break down complex tasks into actionable steps
3. SELECT AND USE appropriate tools to accomplish each step
4. Execute tools and provide results based on actual data
5. Consider security, cost, and performance implications

Always think step-by-step and ALWAYS use tools when available."""
    
    def _build_reasoning_prompt(
        self,
        query: str,
        history: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the reasoning prompt"""
        
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in available_tools
        ])
        
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history[-5:]  # Last 5 messages for context
        ]) if history else "No previous conversation"
        
        context_text = json.dumps(context, indent=2) if context else "No additional context"
        
        return f"""Analyze the following user request and create a detailed action plan.

User Request: {query}

Conversation History:
{history_text}

Additional Context:
{context_text}

Available Tools:
{tools_description}

IMPORTANT: You must respond with a JSON object containing your reasoning and a plan with tool calls.

EXAMPLES OF CORRECT TOOL USAGE:

Example 1 - List EC2 instances:
{{
    "reasoning": "User wants to see EC2 instances. I'll use aws_infrastructure tool.",
    "plan": [
        {{
            "step": 1,
            "tool": "aws_infrastructure",
            "input": {{"action": "list", "service": "ec2"}},
            "rationale": "Query AWS EC2",
            "requires_approval": false
        }}
    ]
}}

Example 2 - List Lambda functions:
{{
    "reasoning": "User wants Lambda functions. I'll use aws_infrastructure tool.",
    "plan": [
        {{
            "step": 1,
            "tool": "aws_infrastructure",
            "input": {{"action": "list", "service": "lambda"}},
            "rationale": "Query AWS Lambda",
            "requires_approval": false
        }}
    ]
}}

Example 3 - Analyze costs:
{{
    "reasoning": "User wants cost analysis. I'll use cost_analysis tool.",
    "plan": [
        {{
            "step": 1,
            "tool": "cost_analysis",
            "input": {{"time_period": "last_month"}},
            "rationale": "Get cost data",
            "requires_approval": false
        }}
    ]
}}

Your response format:
{{
    "reasoning": "Your step-by-step reasoning",
    "plan": [
        {{
            "step": 1,
            "tool": "tool_name",
            "input": {{"param": "value"}},
            "rationale": "Why this step is needed",
            "requires_approval": false
        }}
    ]
}}

CRITICAL RULES:
1. ALWAYS use tools - NEVER suggest manual steps or AWS CLI
2. For ANY AWS resource query, use: aws_infrastructure with action="list"
3. ONLY valid actions for aws_infrastructure: "list" (nothing else!)
4. ONLY valid services: "ec2", "lambda", "s3"
5. For costs: use cost_analysis tool
6. For code: use code_analysis tool

REMEMBER: action must ALWAYS be exactly "list" for aws_infrastructure tool!"""
    
    def _parse_reasoning_output(self, reasoning_text: str) -> Dict[str, Any]:
        """Parse the LLM reasoning output"""
        try:
            # Try to extract JSON from the response
            # LLM might wrap JSON in markdown code blocks
            if "```json" in reasoning_text:
                json_start = reasoning_text.find("```json") + 7
                json_end = reasoning_text.find("```", json_start)
                json_text = reasoning_text[json_start:json_end].strip()
            elif "```" in reasoning_text:
                json_start = reasoning_text.find("```") + 3
                json_end = reasoning_text.find("```", json_start)
                json_text = reasoning_text[json_start:json_end].strip()
            else:
                # Try to find JSON object in the text
                json_start = reasoning_text.find("{")
                json_end = reasoning_text.rfind("}") + 1
                json_text = reasoning_text[json_start:json_end]
            
            parsed = json.loads(json_text)
            
            return {
                "reasoning": parsed.get("reasoning", ""),
                "plan": parsed.get("plan", [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing reasoning output: {e}")
            # Fallback: return the raw text as reasoning
            return {
                "reasoning": reasoning_text,
                "plan": []
            }

