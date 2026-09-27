from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from db.base import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False, default="")

    # draft -> published -> deleted (только в этом направлении, см. api/services.py)
    status = Column(String(20), nullable=False, default="draft")

    # В полях хранится только сгенерированное (латиницей) имя объекта в Minio,
    # а не готовый URL — сам URL собирается на лету, см. storage/minio_client.py
    image_filename = Column(String(255), nullable=True)
    video_filename = Column(String(255), nullable=True)

    kpd = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)

    # Системное поле — не принимается от клиента, вычисляется на бэкенде
    # через core.current_user.get_current_user_id()
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
