from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from core.current_user import get_current_user_id
from models.service import Service
from models.like import Like
from schemas.service import ServiceListItem, ServiceOut, ServicePublishIn, LikeIn, LikeOut
from storage.minio_client import upload_media, build_media_url
from api.common import (
    count_likes,
    get_published,
    get_first_published,
    get_next_published,
    get_draft,
    get_own_service,
    serialize_service,
)

router = APIRouter()


@router.get("", response_model=list[ServiceListItem])
async def list_services(
    kpd_below_than: Optional[int] = Query(default=None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    current_user_id = get_current_user_id()

    stmt = select(Service).where(Service.status == "published")
    if kpd_below_than is not None:
        stmt = stmt.where(Service.kpd <= kpd_below_than)
    result = await db.execute(stmt.order_by(Service.id))
    services = result.scalars().all()

    items = []
    for s in services:
        items.append(
            ServiceListItem(
                id=s.id,
                title=s.title,
                price=s.price,
                kpd=s.kpd,
                image_url=build_media_url(s.image_filename),
                video_url=build_media_url(s.video_filename),
                likes_count=await count_likes(db, s.id),
                is_own=1 if s.creator_id == current_user_id else 0,
            )
        )
    return items


@router.get("/feed", response_model=ServiceOut)
async def get_feed(db: AsyncSession = Depends(get_db)):
    service = await get_first_published(db)
    if service is None:
        raise HTTPException(status_code=404, detail="Нет опубликованных услуг")
    return await serialize_service(db, service, get_current_user_id())


@router.get("/feed/{service_id}", response_model=ServiceOut)
async def get_feed_by_id(
    service_id: int,
    next: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = await get_published(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    if next:
        nxt = await get_next_published(db, service.id)
        if nxt is None:
            raise HTTPException(status_code=404, detail="Следующая услуга не найдена")
        service = nxt

    return await serialize_service(db, service, get_current_user_id())


@router.get("/draft", response_model=Optional[ServiceOut])
async def get_my_draft(db: AsyncSession = Depends(get_db)):
    current_user_id = get_current_user_id()
    draft = await get_draft(db, current_user_id)
    if draft is None:
        return None
    return await serialize_service(db, draft, current_user_id)


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    title: str = Form(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    current_user_id = get_current_user_id()

    existing = await get_draft(db, current_user_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть незавершённый черновик. Опубликуйте или удалите его, прежде чем создавать новый.",
        )

    image_filename = await upload_media(image, "images") if image and image.filename else None
    video_filename = await upload_media(video, "videos") if video and video.filename else None

    service = Service(
        title=title.strip() or "Без названия",
        description="",
        status="draft",
        creator_id=current_user_id,
        image_filename=image_filename,
        video_filename=video_filename,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)

    return await serialize_service(db, service, current_user_id)


@router.put("/{service_id}/publish", response_model=ServiceOut)
async def publish_service(
    service_id: int,
    payload: ServicePublishIn,
    db: AsyncSession = Depends(get_db),
):
    current_user_id = get_current_user_id()

    service = await get_own_service(db, service_id, current_user_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    if service.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Опубликовать можно только услугу в статусе «черновик»",
        )

    if payload.title:
        service.title = payload.title.strip()
    service.description = payload.description.strip()
    service.kpd = payload.kpd
    service.price = payload.price
    service.status = "published"

    await db.commit()
    await db.refresh(service)

    return await serialize_service(db, service, current_user_id)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    current_user_id = get_current_user_id()

    service = await get_own_service(db, service_id, current_user_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    service.status = "deleted"
    await db.commit()
    return None


@router.post("/{service_id}/like", response_model=LikeOut)
async def like_service(
    service_id: int,
    payload: LikeIn,
    db: AsyncSession = Depends(get_db),
):
    current_user_id = get_current_user_id()

    service = await get_published(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    result = await db.execute(
        select(Like).where(Like.service_id == service_id, Like.user_id == current_user_id)
    )
    existing_like = result.scalar_one_or_none()

    if payload.value == 1:
        if existing_like is None:
            db.add(Like(user_id=current_user_id, service_id=service_id))
            await db.commit()
    else:
        if existing_like is not None:
            await db.delete(existing_like)
            await db.commit()

    return LikeOut(
        service_id=service_id,
        liked=payload.value == 1,
        likes_count=await count_likes(db, service_id),
    )
