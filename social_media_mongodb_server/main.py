from fastapi import FastAPI
from .db import connect_to_mongo, close_mongo_connection
from .routes.auth import router as auth_router
from .routes.posts import router as posts_router
from .routes.comments import router as comments_router

app = FastAPI(title="Social Media (MVC)")

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(comments_router)

@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()

