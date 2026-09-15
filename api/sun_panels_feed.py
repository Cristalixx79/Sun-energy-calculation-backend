from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.sun_panels_common import (
    templates,
    count_likes,
    get_published,
    get_first_published,
    get_next_published,
    resolve_media,
    DEFAULT_IMAGE,
    DEFAULT_VIDEO,
)

router = APIRouter(tags=["feed"])


@router.get("/", response_class=HTMLResponse)
async def get_feed(
    request: Request,
    more: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = await get_first_published(db)
    if service is None:
        raise HTTPException(status_code=404, detail="Нет опубликованных услуг")

    return templates.TemplateResponse(
        request=request,
        name="sun_panels_feed.html",
        context={
            "service": service,
            "likes_count": await count_likes(db, service.id),
            "more": more,
            "image_url": resolve_media(service.image_url, DEFAULT_IMAGE),
            "video_url": resolve_media(service.video_url, DEFAULT_VIDEO),
        },
    )


@router.get("/sun_panels_feed/{service_id}", response_class=HTMLResponse)
async def get_feed_by_id(
    request: Request,
    service_id: int,
    next: bool = False,
    more: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = await get_published(db, service_id)
    if service is None:
        # Если не найдена или удалена — открываем первую опубликованную
        service = await get_first_published(db)
        if service is None:
            raise HTTPException(status_code=404, detail="Нет опубликованных услуг")

    if next:
        nxt = await get_next_published(db, service.id)
        if nxt is None:
            raise HTTPException(status_code=404, detail="Следующая услуга не найдена")
        service = nxt

    return templates.TemplateResponse(
        request=request,
        name="sun_panels_feed.html",
        context={
            "service": service,
            "likes_count": await count_likes(db, service.id),
            "more": more,
            "image_url": resolve_media(service.image_url, DEFAULT_IMAGE),
            "video_url": resolve_media(service.video_url, DEFAULT_VIDEO),
        },
    )