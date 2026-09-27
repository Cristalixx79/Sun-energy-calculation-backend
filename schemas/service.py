from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceListItem(BaseModel):
    """Элемент списка/плитки — только опубликованные услуги."""

    id: int
    title: str
    price: Optional[float] = None
    kpd: Optional[int] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    likes_count: int
    is_own: int = Field(..., description="1, если создатель услуги — текущий пользователь, иначе 0")

    model_config = ConfigDict(from_attributes=True)


class ServiceOut(BaseModel):
    """Полное представление услуги (лента, черновик, результат создания/публикации)."""

    id: int
    title: str
    description: str
    status: str
    kpd: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    creator_id: int
    is_own: int
    likes_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServicePublishIn(BaseModel):
    """Тело запроса PUT /api/services/{id}/publish.

    Системные поля (id, status, creator_id, даты) сюда намеренно не входят —
    клиент не может их передать/изменить."""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    kpd: int = Field(..., ge=0, le=100)
    price: float = Field(..., ge=0)


class LikeIn(BaseModel):
    """Тело запроса POST /api/services/{id}/like."""

    value: int = Field(..., ge=0, le=1, description="1 — поставить лайк, 0 — снять лайк")


class LikeOut(BaseModel):
    service_id: int
    liked: bool
    likes_count: int
