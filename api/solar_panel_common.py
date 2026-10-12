"""Общие для домена "услуга" запросы к БД и сериализация в схему ответа.

"Текущий пользователь" приходит из сессии (core.auth): id передаётся в
функции этого модуля параметром, для гостя это None.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.solar_panel_service import Service
from models.solar_panel_like import Like
from schemas.solar_panel_service import ServiceOut
from storage.solar_panel_minio_client import build_media_url


async def count_likes(db: AsyncSession, service_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Like).where(Like.service_id == service_id)
    )
    return result.scalar() or 0


async def user_has_liked(db: AsyncSession, service_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(Like.id).where(Like.service_id == service_id, Like.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def get_published(db: AsyncSession, service_id: int) -> Optional[Service]:
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.status == "published",
        )
    )
    return result.scalar_one_or_none()


async def get_first_published(db: AsyncSession) -> Optional[Service]:
    result = await db.execute(
        select(Service).where(Service.status == "published").order_by(Service.id)
    )
    return result.scalars().first()


async def get_next_published(db: AsyncSession, service_id: int) -> Optional[Service]:
    result = await db.execute(
        select(Service).where(Service.status == "published").order_by(Service.id)
    )
    published = result.scalars().all()
    if not published:
        return None
    for i, s in enumerate(published):
        if s.id == service_id:
            return published[(i + 1) % len(published)]
    return published[0]


async def get_draft(db: AsyncSession, user_id: int) -> Optional[Service]:
    result = await db.execute(
        select(Service).where(
            Service.status == "draft",
            Service.creator_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_service_for_owner(db: AsyncSession, service_id: int, user_id: int) -> Service:
    """Услуга по id для методов создателя (publish/delete).

    404 — услуги нет, она удалена или это чужой черновик (чужие черновики
    не раскрываем); 403 — услуга опубликована, но принадлежит другому."""
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.status != "deleted")
    )
    service = result.scalar_one_or_none()
    if service is None or (service.creator_id != user_id and service.status != "published"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
    if service.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Услуга принадлежит другому пользователю",
        )
    return service


async def serialize_service(
    db: AsyncSession, service: Service, current_user_id: Optional[int]
) -> ServiceOut:
    return ServiceOut(
        id=service.id,
        title=service.title,
        description=service.description,
        status=service.status,
        kpd=service.kpd,
        price=service.price,
        image_url=build_media_url(service.image_filename),
        video_url=build_media_url(service.video_filename),
        creator_id=service.creator_id,
        is_own=1 if current_user_id is not None and service.creator_id == current_user_id else 0,
        likes_count=await count_likes(db, service.id),
        created_at=service.created_at,
        updated_at=service.updated_at,
    )
