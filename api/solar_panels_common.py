from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates

from models.service import Service
from models.like import Like

templates = Jinja2Templates(directory="templates")

DEFAULT_IMAGE = "http://localhost:9000/media/panel1.jpg"
DEFAULT_VIDEO = "http://localhost:9000/media/background1.jpg"

TEST_USER_ID = 1


async def count_likes(db: AsyncSession, service_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Like).where(Like.service_id == service_id)
    )
    return result.scalar() or 0


async def get_published(db: AsyncSession, service_id: int):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.status == "published",
        )
    )
    return result.scalar_one_or_none()


async def get_first_published(db: AsyncSession):
    result = await db.execute(
        select(Service)
        .where(Service.status == "published")
        .order_by(Service.id)
    )
    return result.scalars().first()


async def get_next_published(db: AsyncSession, service_id: int):
    result = await db.execute(
        select(Service)
        .where(Service.status == "published")
        .order_by(Service.id)
    )
    published = result.scalars().all()
    if not published:
        return None
    for i, s in enumerate(published):
        if s.id == service_id:
            return published[(i + 1) % len(published)]
    return published[0]


async def get_draft(db: AsyncSession, user_id: int = TEST_USER_ID):
    result = await db.execute(
        select(Service).where(
            Service.status == "draft",
            Service.creator_id == user_id,
        )
    )
    return result.scalar_one_or_none()


def resolve_media(url: str | None, default: str) -> str:
    return url or default