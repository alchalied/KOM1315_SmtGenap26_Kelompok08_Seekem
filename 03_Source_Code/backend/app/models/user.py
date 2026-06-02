from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    civitas = "civitas"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nim = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.civitas, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_created_at = Column(DateTime, nullable=True)
    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expires = Column(DateTime, nullable=True)

    laporans = relationship("Laporan", back_populates="pelapor", cascade="all, delete-orphan")
    klaims = relationship("Klaim", back_populates="pengklaim", cascade="all, delete-orphan")
    notifikasis = relationship("Notifikasi", back_populates="user", cascade="all, delete-orphan")
