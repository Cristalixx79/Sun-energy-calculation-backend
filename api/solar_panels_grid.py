from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from api.solar_panels_common import solar_panels_templates, solar_panels_services, count_likes

solar_panels_router = APIRouter(tags=["grid"])


@solar_panels_router.get("/solar_panels_cards", response_class=HTMLResponse)
def get_cards(request: Request, kpd_below_than: str = '25'):
    upper_boundary = int(kpd_below_than)

    cards = []
    for s in solar_panels_services:
        if s["status"] != "published":
            continue
        if upper_boundary is not None and not (s["kpd"] <= upper_boundary):
            continue
        cards.append({**s, "likes_count": count_likes(s["id"])})

    no_cards = False
    if len(cards) == 0:
        no_cards = True

    return solar_panels_templates.TemplateResponse(
        request=request,
        name="solar_panels_grid.html",
        context={
            "cards": cards,
            "selected_kpd": kpd_below_than or "",
            "no_cards_found": no_cards,
        },
    )