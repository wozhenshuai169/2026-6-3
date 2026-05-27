from fastapi import FastAPI

from algorithm_service.api.orchestrator import router as orchestrator_router
from algorithm_service.api.ws import router as ws_router
from algorithm_service.core.config import SERVICE_NAME, VERSION, API_PREFIX

app = FastAPI(title=SERVICE_NAME, version=VERSION)

app.include_router(orchestrator_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"service": SERVICE_NAME, "version": VERSION}
