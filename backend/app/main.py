from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.queue import close_arq_pool
from app.core.redis import close_redis
from app.modules.auth.router import router as auth_router
from app.modules.chats.router import router as chats_router
from app.modules.health.router import router as health_router
from app.modules.messages.router import router as messages_router
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup hooks go here (warm caches, etc.)
    yield
    # Shutdown
    await close_redis()
    await close_arq_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Required by Authlib to persist OAuth state across the redirect.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site="lax",
        https_only=settings.cookie_secure,
    )

    for module_router in (
        health_router,
        auth_router,
        users_router,
        chats_router,
        messages_router,
    ):
        app.include_router(module_router, prefix=settings.api_prefix)
    return app


app = create_app()
