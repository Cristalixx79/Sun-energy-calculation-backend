from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.solar_panels_feed import solar_panels_router as solar_panels_feed_router
from api.solar_panels_draft import solar_panels_router as solar_panels_draft_router
from api.solar_panels_grid import solar_panels_router as solar_panels_grid_router

solar_panels_app = FastAPI(title="solar Energy Farm")

solar_panels_app.mount("/static", StaticFiles(directory="static"), name="static")

solar_panels_app.include_router(solar_panels_feed_router)
solar_panels_app.include_router(solar_panels_draft_router)
solar_panels_app.include_router(solar_panels_grid_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:solar_panels_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "templates", "static", "data"],
    )