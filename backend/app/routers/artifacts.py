
from fastapi import APIRouter, HTTPException, Response, File, UploadFile
from fastapi.responses import FileResponse
import os

router = APIRouter()

ARTIFACTS_DIR = os.getenv('ARTIFACTS_DIR', '/tmp/worker-data')

@router.get('/{filename}')
def get_artifact(filename: str):
    path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Not found')
    # serve file directly
    return FileResponse(path)
