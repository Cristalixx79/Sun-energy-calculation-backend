import os
from typing import Optional


class Settings:

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5433"))
    DB_USER: str = os.getenv("DB_USER", "myuser")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "mypassword")
    DB_NAME: str = os.getenv("DB_NAME", "sun_panels_db")

    # --- Minio (хранилище изображений/видео услуг) ---
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "root")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "rootpassword")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "media")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

        # --- Redis (хранилище сессий) ---
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD") or None

    # --- Сессии и cookie ---
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "session_id")
    # Время жизни сессии в секундах (по умолчанию — сутки)
    SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24)))
    # True — отправлять cookie только по HTTPS (включать на боевом стенде)
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"


    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
