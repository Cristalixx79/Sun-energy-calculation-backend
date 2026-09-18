from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.service import Service
from api.solar_panels_common import (
    templates,
    count_likes,
    resolve_media,
    DEFAULT_IMAGE,
    DEFAULT_VIDEO,
)

router = APIRouter(tags=["grid"])


@router.get("/solar_panels_cards", response_class=HTMLResponse)
async def get_cards(
    request: Request,
    kpd: str = None,
    db: AsyncSession = Depends(get_db),
):
    lo, hi = None, None
    if kpd:
        try:
            lo, hi = (int(x) for x in kpd.split("-"))
        except (ValueError, TypeError):
            lo, hi = None, None

    stmt = select(Service).where(Service.status == "published")
    result = await db.execute(stmt)
    services = result.scalars().all()

    cards = []
    for s in services:
        if lo is not None and s.kpd is not None and not (lo <= s.kpd <= hi):
            continue
        cards.append({
            "id": s.id,
            "title": s.title,
            "price": s.price,
            "kpd": s.kpd,
            "image_url": resolve_media(s.image_url, DEFAULT_IMAGE),
            "video_url": resolve_media(s.video_url, DEFAULT_VIDEO),
            "likes_count": await count_likes(db, s.id),
        })

    return templates.TemplateResponse(
        request=request,
        name="solar_panels_grid.html",
        context={
            "cards": cards,
            "selected_kpd": kpd or "",
        },
    )


@router.post("/solar_panels_service/{service_id}/delete")
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
):
    update_query = """
        UPDATE services
        SET status = 'deleted',
            updated_at = NOW()
        WHERE id = :id
    """
    await db.execute(text(update_query), {"id": service_id})
    await db.commit()

    return RedirectResponse(url="/solar_panels_cards", status_code=303)