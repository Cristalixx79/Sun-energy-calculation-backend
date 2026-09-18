from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from api.solar_panels_common import solar_panels_templates, solar_panels_services, count_likes

solar_panels_router = APIRouter(tags=["grid"])


@solar_panels_router.get("/solar_panels_cards", response_class=HTMLResponse)
def get_cards(request: Request, kpd: str = None):
    lo, hi = None, None
    if kpd:
        try:
            lo, hi = (int(x) for x in kpd.split("-"))
        except (ValueError, TypeError):
            lo, hi = None, None  # некорректный ввод игнорируем

    cards = []
    for s in solar_panels_services:
        if s["status"] != "published":
            continue
        if lo is not None and not (lo <= s["kpd"] <= hi):
            continue
        cards.append({**s, "likes_count": count_likes(s["id"])})

    return solar_panels_templates.TemplateResponse(
        request=request,
        name="solar_panels_grid.html",
        context={
            "cards": cards,
            "selected_kpd": kpd or "",
        },
    )