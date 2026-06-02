from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class TipeNotifikasi(str, enum.Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"

class Notifikasi(Base):
    __tablename__ = "notifikasi"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pesan = Column(String(500), nullable=False)
    tipe = Column(Enum(TipeNotifikasi), default=TipeNotifikasi.INFO, nullable=False)
    tanggal_kirim = Column(DateTime, default=func.now(), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="notifikasis")
