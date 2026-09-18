from fastapi.templating import Jinja2Templates
from data.solar_panels_collections import solar_panels_collection

solar_panels_templates = Jinja2Templates(directory="templates")

solar_panels_services = solar_panels_collection["services"]
solar_panels_likes = solar_panels_collection["likes"]


def count_likes(service_id: int) -> int:
    return sum(1 for like in solar_panels_likes if like["service_id"] == service_id)


def get_published(service_id: int):
    for s in solar_panels_services:
        if s["id"] == service_id and s["status"] == "published":
            return s
    return None


def get_first_published():
    for s in solar_panels_services:
        if s["status"] == "published":
            return s
    return None


def get_next_published(service_id: int):
    published = [s for s in solar_panels_services if s["status"] == "published"]
    if not published:
        return None
    for i, s in enumerate(published):
        if s["id"] == service_id:
            return published[(i + 1) % len(published)]
    return published[0]


def get_draft():
    for s in solar_panels_services:
        if s["status"] == "draft":
            return s
    return None