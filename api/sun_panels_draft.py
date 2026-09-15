from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.service import Service
from api.sun_panels_common import templates, get_draft, TEST_USER_ID

router = APIRouter(tags=["draft"])


@router.get("/sun_panels_add", response_class=HTMLResponse)
async def get_add_page(request: Request, db: AsyncSession = Depends(get_db)):
    draft = await get_draft(db, TEST_USER_ID)
    return templates.TemplateResponse(
        request=request,
        name="sun_panels_add.html",
        context={"draft": draft},
    )


@router.post("/sun_panels_draft")
async def create_draft(
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    existing = await get_draft(db, TEST_USER_ID)
    if existing is not None:
        return RedirectResponse(url="/sun_panels_add", status_code=303)

    service = Service(
        title=title.strip() or "Без названия",
        description="",
        status="draft",
        creator_id=TEST_USER_ID,
    )
    db.add(service)
    await db.commit()

    return RedirectResponse(url="/sun_panels_add", status_code=303)


@router.post("/sun_panels_draft/publish")
async def publish_draft(
    title: str = Form(...),
    description: str = Form(""),
    kpd: int = Form(...),
    price: float = Form(...),
    db: AsyncSession = Depends(get_db),
):
    draft = await get_draft(db, TEST_USER_ID)
    if draft is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    draft.title = title.strip() or draft.title
    draft.description = description.strip()
    draft.kpd = kpd
    draft.price = price
    draft.status = "published"

    await db.commit()

    return RedirectResponse(url="/sun_panels_add", status_code=303)