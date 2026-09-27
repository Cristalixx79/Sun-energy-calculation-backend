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
    kpd_below_than: str = '25',
    db: AsyncSession = Depends(get_db),
):
    upper_boundary = int(kpd_below_than)

    stmt = select(Service).where(Service.status == "published")
    result = await db.execute(stmt)
    services = result.scalars().all()

    cards = []
    for s in services:
        if upper_boundary is not None and not (s.kpd <= upper_boundary):
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

    no_cards = False
    if len(cards) == 0:
        no_cards = True

    return templates.TemplateResponse(
        request=request,
        name="solar_panels_grid.html",
        context={
            "cards": cards,
            "selected_kpd": kpd_below_than or "",
            "no_cards_found": no_cards,
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