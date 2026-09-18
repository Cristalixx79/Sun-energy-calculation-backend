from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from api.solar_panels_common import solar_panels_templates, get_draft

solar_panels_router = APIRouter(tags=["draft"])


@solar_panels_router.get("/solar_panels_add", response_class=HTMLResponse)
def get_add_page(request: Request):
    draft = get_draft()
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    return solar_panels_templates.TemplateResponse(
        request=request,
        name="solar_panels_add.html",
        context={"draft": draft},
    )