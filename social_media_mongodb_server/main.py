from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from another_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .db import connect_to_mongo, close_mongo_connection
from .routes.auth import router as auth_router
from .routes.posts import router as posts_router
from .routes.comments import router as comments_router
from .security import jwt_config
from .routes.mcp_proxy import router as mcp_router


app = FastAPI(title="Social Media (MVC)")

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(mcp_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Social Media API with JWT auth",
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # Optional: apply globally (or attach per-route using dependencies)
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

# Global handler for JWT errors (works like auth middleware error layer)
@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()
