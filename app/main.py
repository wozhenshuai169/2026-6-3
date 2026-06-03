from fastapi import FastAPI

from app.api.rooms import router as rooms_router
from app.api.ai import router as ai_router
from app.api.users import router as users_router
from app.api.audio import router as audio_router
from app.api.vision import router as vision_router
from app.api.recommend import router as recommend_router

app = FastAPI()

app.include_router(rooms_router)
app.include_router(ai_router)
app.include_router(users_router)
app.include_router(audio_router)
app.include_router(vision_router)
app.include_router(recommend_router)

@app.get("/")
async def root():
    return {"message": "A5 Backend Running"}
