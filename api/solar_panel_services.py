from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.solar_panel_session import get_db
from core.solar_panel_auth import get_current_user_id, get_optional_user_id
from models.solar_panel_service import Service
from models.solar_panel_like import Like
from schemas.solar_panel_common import ErrorOut
from schemas.solar_panel_service import ServiceListItem, ServiceOut, ServicePublishIn, LikeIn, LikeOut
from storage.solar_panel_minio_client import upload_media, build_media_url
from api.solar_panel_common import (
    count_likes,
    get_published,
    get_first_published,
    get_next_published,
    get_draft,
    get_service_for_owner,
    serialize_service,
)

router = APIRouter()

# Описания ответов для Swagger
R401 = {401: {"model": ErrorOut, "description": "Гость: сессия отсутствует или истекла (нужен вход через POST /api/users/login)"}}
R403 = {403: {"model": ErrorOut, "description": "Услуга принадлежит другому пользователю"}}
R404 = {404: {"model": ErrorOut, "description": "Услуга не найдена (или удалена)"}}
R409 = {409: {"model": ErrorOut, "description": "Недопустимый переход статуса / конфликт состояния"}}

ServiceId = Annotated[int, Path(ge=1, description="Идентификатор услуги", examples=[1])]


# ---------------------------------------------------------------- чтение (гость и создатель)


@router.get(
    "",
    response_model=list[ServiceListItem],
    summary="Список опубликованных услуг (плитка)",
    description=(
        "Возвращает **только опубликованные** услуги (черновики и удалённые не отдаются). "
        "Фильтрация выполняется на бэкенде: `kpd_below_than` — верхняя граница КПД.\n\n"
        "**Доступно всем** — результат не зависит от cookie. Для аутентифицированного "
        "пользователя поле `is_own` = 1 у его услуг, для гостя всегда 0."
    ),
)
async def list_services(
    kpd_below_than: Optional[int] = Query(
        default=None, ge=0, le=100, description="Показать услуги с КПД не выше указанного, %", examples=[25]
    ),
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id),
):
    stmt = select(Service).where(Service.status == "published")
    if kpd_below_than is not None:
        stmt = stmt.where(Service.kpd <= kpd_below_than)
    result = await db.execute(stmt.order_by(Service.id))
    services = result.scalars().all()

    items = []
    for s in services:
        items.append(
            ServiceListItem(
                id=s.id,
                title=s.title,
                price=s.price,
                kpd=s.kpd,
                image_url=build_media_url(s.image_filename),
                video_url=build_media_url(s.video_filename),
                likes_count=await count_likes(db, s.id),
                is_own=1 if current_user_id is not None and s.creator_id == current_user_id else 0,
            )
        )
    return items


@router.get(
    "/feed",
    response_model=ServiceOut,
    summary="Лента: первая опубликованная услуга",
    description="Лента без указания id — первая опубликованная услуга. **Доступно всем.**",
    responses={404: {"model": ErrorOut, "description": "Нет опубликованных услуг"}},
)
async def get_feed(
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id),
):
    service = await get_first_published(db)
    if service is None:
        raise HTTPException(status_code=404, detail="Нет опубликованных услуг")
    return await serialize_service(db, service, current_user_id)


@router.get(
    "/feed/{service_id}",
    response_model=ServiceOut,
    summary="Лента: услуга по id или следующая за ней",
    description=(
        "Возвращает опубликованную услугу с указанным id. С параметром `next=true` "
        "возвращает следующую опубликованную услугу по кругу. **Доступно всем.**"
    ),
    responses=R404,
)
async def get_feed_by_id(
    service_id: ServiceId,
    next: bool = Query(default=False, description="true — перейти к следующей услуге"),
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[int] = Depends(get_optional_user_id),
):
    service = await get_published(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    if next:
        nxt = await get_next_published(db, service.id)
        if nxt is None:
            raise HTTPException(status_code=404, detail="Следующая услуга не найдена")
        service = nxt

    return await serialize_service(db, service, current_user_id)


# ---------------------------------------------------------------- методы создателя


@router.get(
    "/draft",
    response_model=Optional[ServiceOut],
    summary="Черновик текущего пользователя",
    description=(
        "Возвращает черновик аутентифицированного пользователя (id не указывается — "
        "у пользователя не более одного черновика) или `null`, если черновика нет.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses=R401,
)
async def get_my_draft(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    draft = await get_draft(db, current_user_id)
    if draft is None:
        return None
    return await serialize_service(db, draft, current_user_id)


@router.post(
    "",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить услугу (создать черновик)",
    description=(
        "Создаёт черновик услуги и загружает файлы изображения и короткого видео "
        "(`multipart/form-data`). Файлы сохраняются в Minio под сгенерированными "
        "латинскими именами, в БД пишутся только имена.\n\n"
        "Создатель (`creator_id`) **подставляется автоматически** из сессии, "
        "системные поля (id, статус, создатель, даты) с клиента не принимаются.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses={**R401, **R409},
)
async def create_service(
    title: str = Form(..., min_length=1, max_length=100, description="Тип/название панели", examples=["Монокристаллическая панель X1"]),
    image: Optional[UploadFile] = File(None, description="Изображение панели"),
    video: Optional[UploadFile] = File(None, description="Короткое видео панели"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    existing = await get_draft(db, current_user_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть незавершённый черновик. Опубликуйте или удалите его, прежде чем создавать новый.",
        )

    image_filename = await upload_media(image, "images") if image and image.filename else None
    video_filename = await upload_media(video, "videos") if video and video.filename else None

    service = Service(
        title=title.strip() or "Без названия",
        description="",
        status="draft",
        creator_id=current_user_id,  # автозаполнение создателя из сессии
        image_filename=image_filename,
        video_filename=video_filename,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)

    return await serialize_service(db, service, current_user_id)


@router.put(
    "/{service_id}/publish",
    response_model=ServiceOut,
    summary="Опубликовать услугу",
    description=(
        "Публикация: переводит **свой** черновик в статус `published` и сохраняет "
        "описание, КПД и цену. Обратного перехода в черновик не существует.\n\n"
        "Для гостя — `401`; для чужой услуги — `403`; если услуга уже не черновик — `409`.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses={**R401, **R403, **R404, **R409},
)
async def publish_service(
    payload: ServicePublishIn,
    service_id: ServiceId,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    service = await get_service_for_owner(db, service_id, current_user_id)
    if service.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Опубликовать можно только услугу в статусе «черновик»",
        )

    if payload.title:
        service.title = payload.title.strip()
    service.description = payload.description.strip()
    service.kpd = payload.kpd
    service.price = payload.price
    service.status = "published"

    await db.commit()
    await db.refresh(service)

    return await serialize_service(db, service, current_user_id)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить услугу (soft delete)",
    description=(
        "Мягкое удаление: статус услуги меняется на `deleted`, запись остаётся в БД, "
        "но больше не отдаётся клиенту. Только **своя** услуга.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses={**R401, **R403, **R404},
)
async def delete_service(
    service_id: ServiceId,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    service = await get_service_for_owner(db, service_id, current_user_id)
    service.status = "deleted"
    await db.commit()
    return None


@router.post(
    "/{service_id}/like",
    response_model=LikeOut,
    summary="Поставить или снять лайк",
    description=(
        "Лайк от текущего пользователя опубликованной услуге: `value = 1` ставит лайк, "
        "`value = 0` снимает. Повторный вызов ничего не дублирует.\n\n"
        "**Только создатель** (нужна сессия)."
    ),
    responses={**R401, **R404},
)
async def like_service(
    payload: LikeIn,
    service_id: ServiceId,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    service = await get_published(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    result = await db.execute(
        select(Like).where(Like.service_id == service_id, Like.user_id == current_user_id)
    )
    existing_like = result.scalar_one_or_none()

    if payload.value == 1:
        if existing_like is None:
            db.add(Like(user_id=current_user_id, service_id=service_id))
            await db.commit()
    else:
        if existing_like is not None:
            await db.delete(existing_like)
            await db.commit()

    return LikeOut(
        service_id=service_id,
        liked=payload.value == 1,
        likes_count=await count_likes(db, service_id),
    )
