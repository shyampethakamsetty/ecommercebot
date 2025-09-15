
from fastapi import APIRouter, HTTPException
import os, json

router = APIRouter()
STATUS_FILE = os.getenv('PROXY_STATUS_FILE', '/tmp/proxy-status.json')

@router.get('/health')
def proxy_health():
    try:
        if not os.path.exists(STATUS_FILE):
            return {'status':'no-data'}
        with open(STATUS_FILE,'r') as fh:
            data = json.load(fh)
        return {'status':'ok', 'proxies': data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
