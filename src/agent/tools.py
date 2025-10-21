"""
Tool Registry and Implementations
Tools that the agent can use to take actions
"""
import logging
import json
import subprocess
from typing import Dict, Any, List, Optional
import boto3
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of all available tools for the agent"""
    
    def __init__(self):
        self.tools: Dict[str, 'BaseTool'] = {}
    
    async def initialize(self):
        """Initialize all tools"""
        # Register tools
        self.register_tool(AWSInfrastructureTool())
        self.register_tool(CodeAnalysisTool())
        self.register_tool(WebSearchTool())
        self.register_tool(CodeExecutionTool())
        self.register_tool(KnowledgeBaseTool())
        self.register_tool(CostAnalysisTool())
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    def register_tool(self, tool: 'BaseTool'):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get definitions of all tools for LLM"""
        return [tool.get_definition() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        return await tool.execute(tool_input)
    
    async def cleanup(self):
        """Cleanup all tools"""
        for tool in self.tools.values():
            await tool.cleanup()


class BaseTool:
    """Base class for all tools"""
    
    name: str = "base_tool"
    description: str = "Base tool"
    
    def get_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters()
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema"""
        return {}
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool"""
        raise NotImplementedError
    
    async def cleanup(self):
        """Cleanup tool resources"""
        pass


class AWSInfrastructureTool(BaseTool):
    """Tool for managing AWS infrastructure"""
    
    name = "aws_infrastructure"
    description = "Query and manage AWS infrastructure (EC2, Lambda, S3, etc.)"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Action to perform: 'list' (to list/describe resources)",
                "required": True,
                "example": "list"
            },
            "service": {
                "type": "string",
                "description": "AWS service: 'ec2' (for EC2 instances), 'lambda' (for Lambda functions), 's3' (for S3 buckets)",
                "required": True,
                "example": "ec2"
            },
            "resource_id": {
                "type": "string",
                "description": "Specific resource ID (optional, for describe operations)",
                "required": False
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS infrastructure operation"""
        action = tool_input.get('action', '').lower()
        service = tool_input.get('service', '').lower()
        
        if not settings.ENABLE_AWS_ACTIONS:
            return {
                "success": False,
                "message": "AWS actions are disabled in configuration"
            }
        
        try:
            # Normalize action names
            if action in ['list', 'list_instances', 'describe', 'get']:
                action = 'list'
            
            if service == 'ec2' and action == 'list':
                return await self._list_ec2_instances()
            elif service == 'lambda' and action == 'list':
                return await self._list_lambda_functions()
            elif service == 's3' and action == 'list':
                return await self._list_s3_buckets()
            else:
                return {
                    "success": False,
                    "message": f"Unsupported action '{action}' for service '{service}'. Try: action='list', service='ec2'"
                }
        except Exception as e:
            logger.error(f"Error executing AWS tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_ec2_instances(self) -> Dict[str, Any]:
        """List EC2 instances"""
        ec2 = boto3.client('ec2', region_name=settings.AWS_REGION)
        response = ec2.describe_instances()
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'id': instance['InstanceId'],
                    'type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'launch_time': str(instance['LaunchTime'])
                })
        
        return {
            "success": True,
            "instances": instances,
            "count": len(instances)
        }
    
    async def _list_lambda_functions(self) -> Dict[str, Any]:
        """List Lambda functions"""
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)
        response = lambda_client.list_functions()
        
        functions = [
            {
                'name': func['FunctionName'],
                'runtime': func['Runtime'],
                'memory': func['MemorySize'],
                'timeout': func['Timeout']
            }
            for func in response['Functions']
        ]
        
        return {
            "success": True,
            "functions": functions,
            "count": len(functions)
        }
    
    async def _list_s3_buckets(self) -> Dict[str, Any]:
        """List S3 buckets"""
        s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        response = s3.list_buckets()
        
        buckets = [
            {
                'name': bucket['Name'],
                'creation_date': str(bucket['CreationDate'])
            }
            for bucket in response['Buckets']
        ]
        
        return {
            "success": True,
            "buckets": buckets,
            "count": len(buckets)
        }


class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code"""
    
    name = "code_analysis"
    description = "Analyze code for bugs, security issues, and best practices"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "code": {
                "type": "string",
                "description": "Code to analyze",
                "required": True
            },
            "language": {
                "type": "string",
                "description": "Programming language",
                "required": True
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code"""
        code = tool_input.get('code', '')
        language = tool_input.get('language', 'python')
        
        issues = []
        
        # Simple code analysis (in production, use proper linters)
        if language == 'python':
            # Check for common issues
            if 'eval(' in code:
                issues.append({
                    'severity': 'high',
                    'message': 'Use of eval() is a security risk',
                    'line': code.find('eval(')
                })
            
            if 'import *' in code:
                issues.append({
                    'severity': 'medium',
                    'message': 'Wildcard imports are discouraged',
                    'line': code.find('import *')
                })
        
        return {
            "success": True,
            "issues": issues,
            "issue_count": len(issues),
            "recommendations": [
                "Use proper error handling",
                "Add type hints",
                "Include docstrings"
            ]
        }


class WebSearchTool(BaseTool):
    """Tool for searching the web"""
    
    name = "web_search"
    description = "Search the web for documentation, solutions, and information"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query",
                "required": True
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Search the web"""
        query = tool_input.get('query', '')
        
        # In production, integrate with actual search API
        # For demo, return simulated results
        return {
            "success": True,
            "results": [
                {
                    "title": f"Result for: {query}",
                    "url": "https://example.com",
                    "snippet": "Relevant information about the query..."
                }
            ]
        }


class CodeExecutionTool(BaseTool):
    """Tool for executing code safely"""
    
    name = "code_execution"
    description = "Execute code in a sandboxed environment"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "code": {
                "type": "string",
                "description": "Code to execute",
                "required": True
            },
            "language": {
                "type": "string",
                "description": "Programming language",
                "required": True
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code"""
        if not settings.ENABLE_CODE_EXECUTION:
            return {
                "success": False,
                "message": "Code execution is disabled"
            }
        
        # In production, use AWS Lambda or sandboxed environment
        return {
            "success": True,
            "output": "Code execution result would appear here",
            "message": "Code executed successfully (simulated)"
        }


class KnowledgeBaseTool(BaseTool):
    """Tool for querying RAG knowledge base"""
    
    name = "knowledge_base"
    description = "Query internal documentation and knowledge base using RAG"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Query for knowledge base",
                "required": True
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Query knowledge base"""
        query = tool_input.get('query', '')
        
        # In production, integrate with Amazon Bedrock Knowledge Base
        return {
            "success": True,
            "results": [
                {
                    "content": "Relevant documentation content",
                    "source": "internal_docs.md",
                    "relevance_score": 0.95
                }
            ]
        }


class CostAnalysisTool(BaseTool):
    """Tool for analyzing AWS costs"""
    
    name = "cost_analysis"
    description = "Analyze AWS costs and provide optimization recommendations"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "time_period": {
                "type": "string",
                "description": "Time period: last_month, last_week, today",
                "required": True
            }
        }
    
    async def execute(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze costs"""
        try:
            ce = boto3.client('ce', region_name=settings.AWS_REGION)
            
            # Get cost data
            # In production, query actual cost data
            return {
                "success": True,
                "total_cost": 1250.50,
                "top_services": [
                    {"service": "EC2", "cost": 450.25},
                    {"service": "S3", "cost": 125.50},
                    {"service": "Lambda", "cost": 75.00}
                ],
                "recommendations": [
                    "Consider using Reserved Instances for EC2",
                    "Enable S3 Intelligent-Tiering",
                    "Optimize Lambda memory allocation"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

