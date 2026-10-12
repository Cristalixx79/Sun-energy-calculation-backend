import os


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

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
