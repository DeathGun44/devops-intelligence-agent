"""
API Routes for the DevOps Intelligence Agent
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID")
    context: Optional[dict] = Field(default=None, description="Additional context")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    reasoning: str
    actions_taken: list
    requires_approval: bool
    session_id: str
    timestamp: str


class ActionApprovalRequest(BaseModel):
    """Action approval request"""
    session_id: str
    action_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Process a chat message
    
    The agent will:
    1. Analyze the request
    2. Create an action plan
    3. Execute actions (with approval if needed)
    4. Return results
    """
    try:
        agent = req.app.state.agent
        
        result = await agent.process_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve-action")
async def approve_action(request: ActionApprovalRequest, req: Request):
    """
    Approve a pending action
    """
    try:
        agent = req.app.state.agent
        
        result = await agent.approve_action(
            session_id=request.session_id,
            action_id=request.action_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error approving action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, req: Request):
    """
    Get conversation history for a session
    """
    try:
        agent = req.app.state.agent
        history = await agent.conversation_store.get_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools(req: Request):
    """
    Get list of available tools
    """
    try:
        agent = req.app.state.agent
        tools = agent.tool_registry.get_tool_definitions()
        
        return {
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

