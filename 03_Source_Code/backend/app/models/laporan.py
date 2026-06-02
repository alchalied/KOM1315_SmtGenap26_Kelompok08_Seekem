from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base

class JenisLaporan(str, enum.Enum):
    hilang = "hilang"
    ditemukan = "ditemukan"

class StatusLaporan(str, enum.Enum):
    pending = "pending"
    published = "published"
    claimed = "claimed"
    resolved = "resolved"
    rejected = "rejected"

class PublicStatusFilter(str, enum.Enum):
    published = "published"
    resolved = "resolved"

class Laporan(Base):
    __tablename__ = "laporan"

    id = Column(Integer, primary_key=True, index=True)
    pelapor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    jenis_laporan = Column(Enum(JenisLaporan), nullable=False)
    tanggal_kejadian = Column(DateTime, default=datetime.utcnow, nullable=False)
    lokasi = Column(String(255), nullable=False)
    deskripsi = Column(Text, nullable=True)
    
    nama_barang = Column(String(255), nullable=False)
    kategori = Column(String(100), nullable=False)  # Free-text agar cocok dengan kategori FE
    foto_url = Column(String(500), nullable=True)
    
    status = Column(Enum(StatusLaporan), default=StatusLaporan.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship dengan tabel User dan Klaim
    pelapor = relationship("User", back_populates="laporans")
    klaims = relationship("Klaim", back_populates="laporan", cascade="all, delete-orphan")
