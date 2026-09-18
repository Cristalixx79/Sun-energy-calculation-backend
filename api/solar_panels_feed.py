from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from api.solar_panels_common import (
    solar_panels_templates,
    count_likes,
    get_published,
    get_first_published,
    get_next_published,
)

solar_panels_router = APIRouter(tags=["feed"])


@solar_panels_router.get("/", response_class=HTMLResponse)
def get_feed(request: Request, more: bool = False):
    service = get_first_published()
    if service is None:
        raise HTTPException(status_code=404, detail="Нет опубликованных услуг")

    return solar_panels_templates.TemplateResponse(
        request=request,
        name="solar_panels_feed.html",
        context={
            "service": service,
            "likes_count": count_likes(service["id"]),
            "more": more,
        },
    )


@solar_panels_router.get("/solar_panels_feed/{service_id}", response_class=HTMLResponse)
def get_feed_by_id(
    request: Request,
    service_id: int,
    next: bool = False,
    more: bool = False,
    less: bool = False,
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

    return solar_panels_templates.TemplateResponse(
        request=request,
        name="solar_panels_feed.html",
        context={
            "service": service,
            "likes_count": count_likes(service["id"]),
            "more": more,
            "less": less,
        },
    )