from fastapi import FastAPI
from app.routers import auth, workflows, tasks, chat, artifacts, proxy
app = FastAPI(title='Ecomm Orchestrator (extended)')

app.include_router(auth.router, prefix='/api/auth', tags=['auth'])
app.include_router(workflows.router, prefix='/api/workflows', tags=['workflows'])
app.include_router(tasks.router, prefix='/api/tasks', tags=['tasks'])
app.include_router(chat.router, prefix='/api/chat', tags=['chat'])
app.include_router(artifacts.router, prefix='/api/artifacts', tags=['artifacts'])
app.include_router(proxy.router, prefix='/api/proxy', tags=['proxy'])

@app.get('/health')
async def health():
    return {'status':'ok'}
