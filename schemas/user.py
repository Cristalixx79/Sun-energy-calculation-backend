from pydantic import BaseModel, ConfigDict, Field


class UserRegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserLoginIn(BaseModel):
    """Заглушка на лаб. №4 — сейчас реального входа не выполняет."""

    username: str
    password: str
