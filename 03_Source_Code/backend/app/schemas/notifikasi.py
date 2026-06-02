from pydantic import BaseModel
from datetime import datetime
from app.models.notifikasi import TipeNotifikasi

class NotifikasiResponse(BaseModel):
    id: int
    user_id: int
    pesan: str
    tipe: TipeNotifikasi
    tanggal_kirim: datetime
    is_read: bool

    class Config:
        from_attributes = True
