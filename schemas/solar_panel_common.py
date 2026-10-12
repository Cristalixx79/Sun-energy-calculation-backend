from pydantic import BaseModel, Field


class MessageOut(BaseModel):
    message: str = Field(..., examples=["Вы вышли из системы"])


class ErrorOut(BaseModel):
    detail: str = Field(..., examples=["Услуга не найдена"])
