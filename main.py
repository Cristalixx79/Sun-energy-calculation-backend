from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.sun_panels_feed import sun_panels_router as sun_panels_feed_router
from api.sun_panels_draft import sun_panels_router as sun_panels_draft_router
from api.sun_panels_grid import sun_panels_router as sun_panels_grid_router

sun_panels_app = FastAPI(title="Sun Energy Farm")

sun_panels_app.mount("/static", StaticFiles(directory="static"), name="static")

sun_panels_app.include_router(sun_panels_feed_router)
sun_panels_app.include_router(sun_panels_draft_router)
sun_panels_app.include_router(sun_panels_grid_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:sun_panels_app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "templates", "static", "data"],
    )