"""
Tests for DevOps Intelligence Agent
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agent.bedrock_agent import DevOpsAgent
from src.agent.reasoning import ReasoningEngine
from src.agent.tools import ToolRegistry


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization"""
    agent = DevOpsAgent()
    
    with patch('boto3.client'):
        await agent.initialize()
        
        assert agent.bedrock_runtime is not None
        assert agent.tool_registry is not None
        assert agent.reasoning_engine is not None


@pytest.mark.asyncio
async def test_process_message():
    """Test message processing"""
    agent = DevOpsAgent()
    agent.bedrock_runtime = Mock()
    agent.reasoning_engine = Mock()
    agent.reasoning_engine.reason = AsyncMock(return_value={
        'reasoning': 'Test reasoning',
        'plan': []
    })
    agent.conversation_store = Mock()
    agent.conversation_store.get_history = AsyncMock(return_value=[])
    agent.conversation_store.add_message = AsyncMock()
    
    result = await agent.process_message(
        message="List EC2 instances",
        session_id="test-session"
    )
    
    assert 'message' in result
    assert 'session_id' in result
    assert result['session_id'] == "test-session"


@pytest.mark.asyncio
async def test_tool_registry():
    """Test tool registry"""
    registry = ToolRegistry()
    await registry.initialize()
    
    tools = registry.get_tool_definitions()
    
    assert len(tools) > 0
    assert any(tool['name'] == 'aws_infrastructure' for tool in tools)
    assert any(tool['name'] == 'code_analysis' for tool in tools)


def test_reasoning_prompt_building():
    """Test reasoning prompt building"""
    engine = ReasoningEngine(Mock(), "test-model")
    
    prompt = engine._build_reasoning_prompt(
        query="Test query",
        history=[],
        available_tools=[],
        context=None
    )
    
    assert "Test query" in prompt
    assert "Available Tools" in prompt

