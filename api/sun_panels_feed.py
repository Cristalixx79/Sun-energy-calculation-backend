from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from api.sun_panels_common import (
    sun_panels_templates,
    count_likes,
    get_published,
    get_first_published,
    get_next_published,
)

sun_panels_router = APIRouter(tags=["feed"])


@sun_panels_router.get("/", response_class=HTMLResponse)
def get_feed(request: Request, more: bool = False):
    service = get_first_published()
    if service is None:
        raise HTTPException(status_code=404, detail="Нет опубликованных услуг")

    return sun_panels_templates.TemplateResponse(
        request=request,
        name="sun_panels_feed.html",
        context={
            "service": service,
            "likes_count": count_likes(service["id"]),
            "more": more,
        },
    )


@sun_panels_router.get("/sun_panels_feed/{service_id}", response_class=HTMLResponse)
def get_feed_by_id(
    request: Request,
    service_id: int,
    next: bool = False,
    more: bool = False,
):
    service = get_published(service_id)
    if service is None:
        service = get_first_published()
        if service is None:
            raise HTTPException(status_code=404, detail="Нет опубликованных услуг")

    if next:
        service = get_next_published(service["id"])
        if service is None:
            raise HTTPException(status_code=404, detail="Следующая услуга не найдена")

    return sun_panels_templates.TemplateResponse(
        request=request,
        name="sun_panels_feed.html",
        context={
            "service": service,
            "likes_count": count_likes(service["id"]),
            "more": more,
        },
    )