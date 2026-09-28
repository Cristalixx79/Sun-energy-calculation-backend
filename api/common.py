from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.service import Service
from models.like import Like
from schemas.service import ServiceOut
from storage.minio_client import build_media_url


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


async def get_own_service(db: AsyncSession, service_id: int, user_id: int) -> Optional[Service]:
    """Услуга по id, но только если она принадлежит указанному пользователю
    (используется для publish/delete — свои услуги, любой статус кроме deleted)."""
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.creator_id == user_id,
            Service.status != "deleted",
        )
    )
    return result.scalar_one_or_none()


async def serialize_service(db: AsyncSession, service: Service, current_user_id: int) -> ServiceOut:
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
        is_own=1 if service.creator_id == current_user_id else 0,
        likes_count=await count_likes(db, service.id),
        created_at=service.created_at,
        updated_at=service.updated_at,
    )
