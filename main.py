from fastapi import FastAPI
import uvicorn

from api.services import router as services_router
from api.users import router as users_router

solar_panels_app = FastAPI(
    title="Solar Panels Service API",
    description="Backend REST API (домены: услуга, пользователь) для SPA «Vibes».",
)

solar_panels_app.include_router(services_router, prefix="/api/services", tags=["services"])
solar_panels_app.include_router(users_router, prefix="/api/users", tags=["users"])

if __name__ == "__main__":
    uvicorn.run(
        "main:solar_panels_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "models", "db", "core", "schemas", "storage"],
    )
