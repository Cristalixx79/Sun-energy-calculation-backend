"""
Хранилище сессий в Redis.

Схема хранения:
    ключ     session:<session_id>
    значение JSON {"user_id": 1, "username": "test_user"}
    TTL      settings.SESSION_TTL_SECONDS

В cookie браузеру отдаётся только случайный session_id — сам пользователь
хранится на сервере, поэтому подделать или "разобрать" cookie нельзя, а
выход из системы (logout) сводится к удалению ключа из Redis.

Посмотреть сессии можно через redis-cli:
    KEYS session:*
    GET session:<session_id>
    TTL session:<session_id>
"""

import json
import secrets
from typing import Optional

import redis.asyncio as aioredis

from core.solar_panel_config import settings

_SESSION_PREFIX = "session:"

_redis: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def _key(session_id: str) -> str:
    return f"{_SESSION_PREFIX}{session_id}"


async def create_session(user_id: int, username: str) -> str:
    """Создаёт сессию и возвращает session_id для записи в cookie."""
    session_id = secrets.token_urlsafe(32)
    payload = json.dumps({"user_id": user_id, "username": username})
    await get_redis().set(_key(session_id), payload, ex=settings.SESSION_TTL_SECONDS)
    return session_id


async def get_session(session_id: str) -> Optional[dict]:
    """Возвращает данные сессии или None, если её нет / она истекла."""
    raw = await get_redis().get(_key(session_id))
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        int(data["user_id"])
    except (ValueError, KeyError, TypeError):
        return None
    return data


async def delete_session(session_id: str) -> None:
    await get_redis().delete(_key(session_id))
