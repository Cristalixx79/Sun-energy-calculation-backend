from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from core.security import hash_password
from models.user import User
from schemas.user import UserRegisterIn, UserOut, UserLoginIn

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterIn, db: AsyncSession = Depends(get_db)):
    """POST /api/users/register — регистрация нового пользователя."""
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


@router.post("/login")
async def login(payload: UserLoginIn):
    """POST /api/users/login — заглушка аутентификации (реализуется в лаб. №4)."""
    return {
        "detail": "Аутентификация будет реализована в лабораторной работе №4",
        "username": payload.username,
    }


@router.post("/logout")
async def logout():
    """POST /api/users/logout — заглушка деавторизации (реализуется в лаб. №4)."""
    return {"detail": "Деавторизация будет реализована в лабораторной работе №4"}
