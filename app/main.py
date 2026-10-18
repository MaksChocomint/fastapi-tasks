import logging
import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.routers import tasks, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Добавляет заголовок X-Process-Time и пишет запрос в лог."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        logger.info(
            "%s %s %s %.4f s", request.method, request.url.path, response.status_code, elapsed
        )
        return response


app = FastAPI(title="Менеджер задач")
app.add_middleware(ProcessTimeMiddleware)
app.include_router(users.router)
app.include_router(tasks.router)
