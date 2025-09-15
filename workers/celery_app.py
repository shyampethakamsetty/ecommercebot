import os
from celery import Celery
BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
celery_app = Celery('worker', broker=BROKER_URL, backend=BROKER_URL, include=['workers.worker.tasks'])
celery_app.conf.task_routes = {'worker.tasks.*': {'queue': 'workers'}}
