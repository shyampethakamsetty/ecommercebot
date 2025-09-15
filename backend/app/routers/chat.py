from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.langchain_adapter import parse_with_fallback
from app.services.task_queue import enqueue_workflow

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: int = 1
    confirm: bool = False

class ChatResponse(BaseModel):
    task_id: str = None
    status: str = "parsed"
    plan: dict = None

@router.post('/query', response_model=ChatResponse)
async def query_chat(req: ChatRequest):
    # parse intent/entities
    parsed = parse_with_fallback(req.query)
    # Map parsed to workflow name and params
    action = parsed.get('action', 'search')
    params = {"filters": parsed.get("filters", {}), "category": parsed.get("category", ""), "raw": req.query, "action": action}
    # If action is dangerous (checkout) and not confirmed, ask for confirmation
    if parsed.get('safe', False) and not req.confirm:
        return ChatResponse(task_id=None, status="requires_confirmation", plan=parsed)
    # enqueue workflow
    task_id = enqueue_workflow(1, params, req.user_id)  # using workflow_id=1 as generic; adapt later
    return ChatResponse(task_id=task_id, status="queued", plan=parsed)