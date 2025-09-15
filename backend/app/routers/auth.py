from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post('/login')
async def login(req: LoginRequest):
    # placeholder - implement real auth
    return {'access_token': 'demo-token', 'token_type': 'bearer'}
