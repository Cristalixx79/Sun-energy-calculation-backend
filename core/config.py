class Settings:
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_USER: str = "myuser"
    DB_PASSWORD: str = "mypassword"
    DB_NAME: str = "sun_panels_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()