from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
import uvicorn

from api.solar_panel_services import router as services_router
from api.solar_panel_users import router as users_router
from storage.solar_panel_session_store import close_redis

API_DESCRIPTION = """
Backend REST API — сервис объявлений о солнечных панелях.

**Как авторизоваться в Swagger**

1. `POST /api/users/register` — зарегистрируйте пользователя (если ещё нет).
2. `POST /api/users/login` — выполните вход. Сервер создаст сессию в Redis и
   выставит cookie `session_id`; браузер будет отправлять её автоматически.
3. Методы с замком (черновик, добавление, публикация, удаление, лайк, выход) — методы
   создателя. Без сессии они возвращают `401`. Методы чтения (список, лента) и
   регистрация/вход доступны без авторизации.
"""

TAGS_METADATA = [
    {
        "name": "users",
        "description": "Регистрация, вход и выход. Сессии хранятся в Redis, идентификатор сессии — в cookie.",
    },
    {
        "name": "services",
        "description": "Услуги (солнечные панели). Чтение доступно гостю, методы создателя — только после входа.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


solar_panels_app = FastAPI(
    title="Solar Panels Service API",
    description=API_DESCRIPTION,
    version="0.4.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)


@solar_panels_app.exception_handler(RedisError)
async def redis_unavailable_handler(request: Request, exc: RedisError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Хранилище сессий (Redis) недоступно"},
    )


solar_panels_app.include_router(services_router, prefix="/api/solar_panel_services", tags=["services"])
solar_panels_app.include_router(users_router, prefix="/api/solar_panel_users", tags=["users"])

if __name__ == "__main__":
    uvicorn.run(
        "main:solar_panels_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "models", "db", "core", "schemas", "storage"],
    )
