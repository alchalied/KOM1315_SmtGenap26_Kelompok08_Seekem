from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base
from app.utils.encryption import EncryptedString

class StatusKlaim(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Klaim(Base):
    __tablename__ = "klaim"

    id = Column(Integer, primary_key=True, index=True)
    laporan_id = Column(Integer, ForeignKey("laporan.id"), nullable=False)
    pengklaim_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    tanggal_klaim = Column(DateTime, default=datetime.utcnow, nullable=False)
    alasan_klaim = Column(Text, nullable=False)
    bukti_foto_url = Column(String(500), nullable=True)
    
    # Kolom tambahan sesuai kontrak FE (ClaimItem.jsx)
    owner_name = Column(String(255), nullable=True)
    nim = Column(String(50), nullable=True)
    faculty = Column(String(255), nullable=True)
    contact = Column(EncryptedString(512), nullable=True)
    
    status_klaim = Column(Enum(StatusKlaim), default=StatusKlaim.pending, nullable=False)
    
    # Relationships
    laporan = relationship("Laporan", back_populates="klaims")
    pengklaim = relationship("User", back_populates="klaims")
