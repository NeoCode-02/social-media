import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, request_id_var
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.queue import close_arq_pool
from app.core.redis import close_redis
from app.modules.admin.router import reports_router
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.chats.router import router as chats_router
from app.modules.follows.router import router as follows_router
from app.modules.health.router import router as health_router
from app.modules.messages.router import router as messages_router
from app.modules.notifications.router import router as notifications_router
from app.modules.posts.router import router as posts_router
from app.modules.posts.router import user_router as user_posts_router
from app.modules.realtime.manager import pubsub_listener
from app.modules.realtime.router import router as realtime_router
from app.modules.relations.router import router as relations_router
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the Redis pub/sub fan-out listener for this process.
    listener = asyncio.create_task(pubsub_listener())
    yield
    # Shutdown
    listener.cancel()
    try:
        await listener
    except asyncio.CancelledError:
        pass
    await close_redis()
    await close_arq_pool()


def create_app() -> FastAPI:
    configure_logging("DEBUG" if settings.debug else "INFO")
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Inner → outer. RequestContext is added last so it wraps everything and
    # always stamps the X-Request-ID / logs the final status.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        same_site="lax",
        https_only=settings.cookie_secure,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(Exception)
    async def on_unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = request_id_var.get(None)
        logging.getLogger("app.error").exception("unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": rid},
            headers={"X-Request-ID": rid} if rid else None,
        )

    for module_router in (
        health_router,
        auth_router,
        users_router,
        chats_router,
        messages_router,
        posts_router,
        user_posts_router,
        follows_router,
        notifications_router,
        relations_router,
        admin_router,
        reports_router,
    ):
        app.include_router(module_router, prefix=settings.api_prefix)
    # WebSocket lives at /ws (no /api prefix) to match the frontend proxy.
    app.include_router(realtime_router)
    return app


app = create_app()
