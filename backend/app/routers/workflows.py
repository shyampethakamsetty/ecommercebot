from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.deps import get_current_user
from app.services.task_queue import enqueue_workflow
router = APIRouter()

class RunRequest(BaseModel):
    workflow_id: int
    params: dict = {}

@router.post('/run')
async def run_workflow(req: RunRequest, user=Depends(get_current_user)):
    task_id = enqueue_workflow(req.workflow_id, req.params, getattr(user, 'id', None))
    return {'task_id': task_id, 'status': 'queued'}
