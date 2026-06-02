from pydantic import BaseModel
from typing import List, Dict, Any

class KategoriDistribution(BaseModel):
    kategori: str
    count: int

class TrafficData(BaseModel):
    tanggal: str
    laporan_masuk: int

class RecentActivity(BaseModel):
    id: int
    tipe: str # "Laporan" atau "Klaim"
    pesan: str
    waktu: str
    status: str

class DashboardStatsResponse(BaseModel):
    total_laporan: int
    total_diverifikasi: int
    total_pending: int
    total_klaim_masuk: int
    distribusi_kategori: List[KategoriDistribution]
    traffic_laporan: List[TrafficData]
    recent_activities: List[RecentActivity]

    class Config:
        from_attributes = True
