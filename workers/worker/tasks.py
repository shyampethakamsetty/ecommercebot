
from workers.celery_app import celery_app
from celery.utils.log import get_task_logger
import requests, os, json
from .workflows import WorkflowManager

logger = get_task_logger(__name__)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')

@celery_app.task(name='worker.tasks.run_workflow_task', bind=True)
def run_workflow_task(self, workflow_id, user_id, params):
    task_id = self.request.id
    logger.info(f"Running workflow {workflow_id} for user {user_id} with params {params} (task_id={task_id})")
    manager = WorkflowManager()
    try:
        action = params.get('action') if params else 'search'
        result = manager.run_composite(action, params or {})
        logger.info(f"Workflow result for task {task_id}: {result}")
        # POST result back to backend for persistence and UI consumption
        try:
            url = f"{BACKEND_URL}/api/tasks/{task_id}/result"
            payload = {'task_id': task_id, 'workflow_id': workflow_id, 'user_id': user_id, 'params': params, 'result': result}
            headers = {'Content-Type': 'application/json'}
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception as e:
            logger.warning(f"Failed to POST result back to backend: {e}")
        return result
    except Exception as e:
        logger.exception(f"Workflow {workflow_id} failed: {e}")
        # post failure
        try:
            url = f"{BACKEND_URL}/api/tasks/{task_id}/result"
            payload = {'task_id': task_id, 'workflow_id': workflow_id, 'user_id': user_id, 'params': params, 'result': {'error': str(e)}}
            headers = {'Content-Type': 'application/json'}
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception as ee:
            logger.warning(f"Failed to POST failure back to backend: {ee}")
        raise
