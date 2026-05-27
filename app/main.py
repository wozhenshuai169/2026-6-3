from fastapi import FastAPI

from app.api.rooms import router as rooms_router
from app.api.ai import router as ai_router
from app.api.users import router as users_router

app = FastAPI()

app.include_router(rooms_router)
app.include_router(ai_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "A5 Backend Running"}
