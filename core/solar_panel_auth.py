"""
Авторизация через серверные сессии и cookie.

Зависимости, которые используют роутеры:

* get_optional_user_id — для публичных методов (чтение). Гость без cookie
  не вызывает Redis вообще; в OpenAPI не добавляет "замок", потому что cookie
  читается напрямую из Request.
* get_current_user_id — для методов создателя. Использует схему безопасности
  APIKeyCookie, поэтому Swagger показывает у этих методов замок, а гость
  получает 401.

Замена singleton-функции из лаб. №3: id пользователя теперь берётся из
сессии, а не из константы.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie

from core.solar_panel_config import settings
from storage.solar_panel_session_store import get_session

session_cookie_scheme = APIKeyCookie(
    name=settings.SESSION_COOKIE_NAME,
    scheme_name="SessionCookie",
    description=(
        "Идентификатор сессии. Выставляется сервером в cookie после "
        "POST /api/users/login и отправляется браузером автоматически."
    ),
    auto_error=False,
)


async def _user_id_from_session(session_id: Optional[str]) -> Optional[int]:
    if not session_id:
        return None
    session = await get_session(session_id)
    if session is None:
        return None
    return int(session["user_id"])


async def get_optional_user_id(request: Request) -> Optional[int]:
    """id пользователя из сессии или None для гостя."""
    return await _user_id_from_session(request.cookies.get(settings.SESSION_COOKIE_NAME))


async def get_current_user_id(
    session_id: Optional[str] = Depends(session_cookie_scheme),
) -> int:
    """id аутентифицированного пользователя; для гостя — 401."""
    user_id = await _user_id_from_session(session_id)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация: сессия отсутствует или истекла",
        )
    return user_id
