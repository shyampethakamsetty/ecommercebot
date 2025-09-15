from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from app.deps import SessionLocal
from app.models.models import Task as TaskModel
from sqlalchemy.orm import Session
import json, os

router = APIRouter()

class TaskResultPayload(BaseModel):
    task_id: str
    workflow_id: int = None
    user_id: int = None
    params: dict = None
    result: dict = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{task_id}/result")
def post_task_result(task_id: str, payload: TaskResultPayload, db: Session = Depends(get_db)):
    # upsert a Task row by task_id (store result JSON and status)
    try:
        # find existing task by id (if stored previously)
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            # create new Task entry
            task = TaskModel(id=task_id, workflow_id=payload.workflow_id or 0)
            db.add(task)
        # update fields
        task.status = payload.result.get('status', 'finished') if payload.result else 'finished'
        task.result = json.dumps(payload.result or {})
        import datetime
        task.finished_at = datetime.datetime.utcnow()
        db.commit()
        return {"status":"ok", "task_id": task_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return {"status":"not_found", "task_id": task_id}
        return {"status":"ok", "task_id": task_id, "db": {"id": task.id, "status": task.status, "result": json.loads(task.result) if task.result else None, "finished_at": task.finished_at.isoformat() if task.finished_at else None}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
