from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from api.sun_panels_common import sun_panels_templates, get_draft

sun_panels_router = APIRouter(tags=["draft"])


@sun_panels_router.get("/sun_panels_add", response_class=HTMLResponse)
def get_add_page(request: Request):
    draft = get_draft()
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    return sun_panels_templates.TemplateResponse(
        request=request,
        name="sun_panels_add.html",
        context={"draft": draft},
    )