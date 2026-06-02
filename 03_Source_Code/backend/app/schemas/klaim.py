from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.klaim import StatusKlaim

class KlaimCreate(BaseModel):
    laporan_id: int
    alasan_klaim: str
    bukti_foto_url: Optional[str] = None

class KlaimVerify(BaseModel):
    is_approved: bool

# Nested schema untuk return data User sebagai pengklaim
class PengklaimBase(BaseModel):
    id: int
    name: str
    email: str
    nim: str
    
    class Config:
        from_attributes = True

# Nested schema untuk return data Laporan yang diklaim
class LaporanKlaimBase(BaseModel):
    id: int
    nama_barang: str
    jenis_laporan: str
    
    class Config:
        from_attributes = True

class KlaimResponse(BaseModel):
    id: int
    laporan_id: int
    pengklaim_id: int
    tanggal_klaim: datetime
    alasan_klaim: str
    bukti_foto_url: Optional[str] = None
    status_klaim: StatusKlaim
    
    pengklaim: Optional[PengklaimBase] = None
    laporan: Optional[LaporanKlaimBase] = None

    class Config:
        from_attributes = True
