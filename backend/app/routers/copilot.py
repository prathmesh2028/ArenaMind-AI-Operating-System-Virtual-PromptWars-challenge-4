from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser, require_staff
from app.services.gemini import gemini_agent_service

router = APIRouter(prefix="/copilot", tags=["Copilot Agents"])

class CopilotChatRequest(BaseModel):
    agent_id: str = Field(..., description="The ID of the specialized agent (e.g. crowd, volunteer, medical, security, accessibility, transportation, sustainability, executive)")
    message: str = Field(..., description="The message query to the agent")
    context: Optional[dict] = Field(None, description="Optional custom dictionary context")

@router.post("/chat", summary="Interact with a specialized operations copilot agent (Streaming response)")
async def chat_with_agent(
    payload: CopilotChatRequest,
    _: CurrentUser = Depends(require_staff)
):
    """
    Establish a streaming chat connection with a specialized operations agent.
    Valid agent_ids: crowd, volunteer, medical, security, accessibility, transportation, sustainability, executive.
    """
    async def event_generator():
        async for chunk in gemini_agent_service.chat_stream(
            agent_id=payload.agent_id,
            message=payload.message,
            context=payload.context
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")
