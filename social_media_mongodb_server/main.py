from fastapi import FastAPI

from .db import connect_to_mongo, close_mongo_connection
from .routes_posts import router as posts_router

app = FastAPI(
    title="Social Media MongoDB Server",
    description="Simple posts + comments API using FastAPI & MongoDB",
    version="0.1.0",
)


@app.on_event("startup")
async def on_startup():
    connect_to_mongo()


@app.on_event("shutdown")
async def on_shutdown():
    close_mongo_connection()


app.include_router(posts_router)
