from sqlalchemy import Column, Integer, String
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    # Хранится PBKDF2-хэш, не сам пароль (см. core/security.py)
    password_hash = Column(String(255), nullable=False)
