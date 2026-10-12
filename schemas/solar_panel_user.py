from pydantic import BaseModel, ConfigDict, Field


class UserRegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Уникальное имя пользователя")
    password: str = Field(..., min_length=6, max_length=128, description="Пароль (хранится только в виде хэша)")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"username": "test_user", "password": "SuperSecret123"}]}
    )


class UserLoginIn(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"username": "test_user", "password": "SuperSecret123"}]}
    )


class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
