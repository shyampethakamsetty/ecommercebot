from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.langchain_adapter import parse_with_fallback, parse
from app.services.task_queue import enqueue_workflow

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: int = 1
    confirm: bool = False

class ChatResponse(BaseModel):
    task_id: Optional[str] = None
    status: str = "parsed"
    plan: Optional[Dict[Any, Any]] = None
    message: Optional[str] = None

@router.post('/query', response_model=ChatResponse)
async def query_chat(req: ChatRequest):
    # Use enhanced LLM parsing for intelligent intent recognition
    parsed = parse(req.query, prefer_llm=True)  # This will try LLM first, fallback to enhanced rules
    
    # Map parsed to workflow name and params
    action = parsed.get('action', 'search')
    
    # Check for missing credentials on checkout actions
    credentials = parsed.get("credentials", {})
    
    # Fallback: try to extract credentials from the raw query if LLM missed them
    if action == "checkout" and (not credentials.get("email") or not credentials.get("password")):
        import re
        raw_query = req.query.lower()
        
        # Try to extract email
        email_match = re.search(r'email\s*:\s*([^\s,]+@[^\s,]+)', raw_query)
        if not email_match:
            email_match = re.search(r'([^\s,]+@[^\s,]+)', raw_query)
        
        # Try to extract password
        password_match = re.search(r'(?:pass|password|pwd)\s*:\s*([^\s,]+)', raw_query)
        
        if email_match and password_match:
            credentials = {
                "email": email_match.group(1) if email_match else None,
                "password": password_match.group(1) if password_match else None
            }

    
    # Still missing credentials after fallback?
    if action == "checkout" and (not credentials.get("email") or not credentials.get("password")):
        return ChatResponse(
            task_id=None, 
            status="needs_credentials", 
            plan=parsed,
            message="I'd be happy to help you purchase those items! However, I need your login credentials to proceed with the checkout. Please provide them in this format: 'buy [items] with email: your@email.com password: yourpassword'"
        )
    
    # Enhanced parameter mapping
    params = {
        "filters": parsed.get("filters", {}), 
        "category": parsed.get("category", ""), 
        "subcategory": parsed.get("subcategory", ""),
        "credentials": credentials,
        "raw": req.query, 
        "action": action,
        "query": parsed.get("filters", {}).get("query", req.query)
    }
    
    # Safety confirmation disabled for testing environment
    # if parsed.get('safe', False) and not req.confirm:
    #     return ChatResponse(task_id=None, status="requires_confirmation", plan=parsed)
    
    # enqueue workflow
    task_id = enqueue_workflow(1, params, req.user_id)  # using workflow_id=1 as generic; adapt later
    return ChatResponse(task_id=task_id, status="queued", plan=parsed)