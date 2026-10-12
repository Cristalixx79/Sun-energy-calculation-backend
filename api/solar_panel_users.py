from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.solar_panel_session import get_db
from core.solar_panel_auth import get_current_user_id, session_cookie_scheme
from core.solar_panel_config import settings
from core.solar_panel_security import hash_password, verify_password
from models.solar_panel_user import User
from schemas.solar_panel_common import ErrorOut, MessageOut
from schemas.solar_panel_user import UserRegisterIn, UserOut, UserLoginIn
from storage.solar_panel_session_store import create_session, delete_session

router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация",
    description=(
        "Создаёт нового пользователя. Пароль сохраняется только в виде PBKDF2-хэша. "
        "Вход после регистрации не выполняется — для этого нужен `POST /api/users/login`.\n\n"
        "**Доступно всем.**"
    ),
    responses={409: {"model": ErrorOut, "description": "Имя пользователя уже занято"}},
)
async def register(payload: UserRegisterIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже существует",
        )

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=UserOut,
    summary="Аутентификация",
    description=(
        "Проверяет имя и пароль, создаёт сессию в Redis и выставляет cookie "
        f"`{settings.SESSION_COOKIE_NAME}` (HttpOnly). После этого браузер сам "
        "отправляет cookie с остальными запросами, и становятся доступны методы создателя. "
        "Для Insomnia/Postman значение cookie можно скопировать из вкладки "
        "Application браузера в заголовок `Cookie`.\n\n"
        "**Доступно всем.**"
    ),
    responses={401: {"model": ErrorOut, "description": "Неверное имя пользователя или пароль"}},
)
async def login(
    payload: UserLoginIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )

    # Повторный вход: старую сессию из cookie (если есть) закрываем
    old_session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if old_session_id:
        await delete_session(old_session_id)

    session_id = await create_session(user.id, user.username)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return user


@router.post(
    "/logout",
    response_model=MessageOut,
    summary="Деавторизация",
    description=(
        "Удаляет сессию из Redis и очищает cookie. Для гостя — `401`.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses={401: {"model": ErrorOut, "description": "Гость: сессия отсутствует или истекла"}},
)
async def logout(
    response: Response,
    session_id: Optional[str] = Depends(session_cookie_scheme),
    _user_id: int = Depends(get_current_user_id),
):
    if session_id:
        await delete_session(session_id)
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
    return MessageOut(message="Вы вышли из системы")
