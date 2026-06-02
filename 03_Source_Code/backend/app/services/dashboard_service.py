from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.laporan import Laporan, StatusLaporan
from app.models.klaim import Klaim, StatusKlaim
from app.schemas.dashboard import (
    DashboardStatsResponse, 
    KategoriDistribution, 
    TrafficData, 
    RecentActivity
)

class DashboardService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> DashboardStatsResponse:
        # 1. Empat Metrik Utama
        total_laporan = db.query(func.count(Laporan.id)).scalar() or 0
        
        total_diverifikasi = db.query(func.count(Laporan.id))\
            .filter(Laporan.status.in_([StatusLaporan.published, StatusLaporan.resolved])).scalar() or 0
            
        total_pending = db.query(func.count(Laporan.id))\
            .filter(Laporan.status == StatusLaporan.pending).scalar() or 0
            
        total_klaim_masuk = db.query(func.count(Klaim.id))\
            .filter(Klaim.status_klaim == StatusKlaim.pending).scalar() or 0
            
        # 2. Distribusi Kategori (Group By)
        dist_query = db.query(Laporan.kategori, func.count(Laporan.id))\
            .group_by(Laporan.kategori).all()
        distribusi_kategori = [
            KategoriDistribution(kategori=row[0], count=row[1]) for row in dist_query
        ]
        
        # 3. Traffic 7 Hari Terakhir
        tujuh_hari_lalu = datetime.utcnow() - timedelta(days=7)
        # Menggunakan ekstrak tanggal sederhana (CAST ke Date sering digunakan di PostgreSQL)
        traffic_query = db.query(
            func.date(Laporan.created_at).label('tanggal'),
            func.count(Laporan.id).label('jumlah')
        ).filter(Laporan.created_at >= tujuh_hari_lalu)\
         .group_by(func.date(Laporan.created_at))\
         .order_by(func.date(Laporan.created_at).asc()).all()
         
        traffic_laporan = [
            TrafficData(tanggal=str(row[0]), laporan_masuk=row[1]) for row in traffic_query
        ]
        
        # 4. Recent Activities (Campuran Laporan & Klaim)
        # Ambil 5 Laporan terbaru
        recent_laporans = db.query(Laporan).order_by(Laporan.created_at.desc()).limit(5).all()
        # Ambil 5 Klaim terbaru
        recent_klaims = db.query(Klaim).order_by(Klaim.tanggal_klaim.desc()).limit(5).all()
        
        activities = []
        for lap in recent_laporans:
            activities.append(RecentActivity(
                id=lap.id,
                tipe="Laporan",
                pesan=f"Laporan baru: {lap.nama_barang}",
                waktu=lap.created_at.isoformat(),
                status=lap.status.value
            ))
        for klm in recent_klaims:
            activities.append(RecentActivity(
                id=klm.id,
                tipe="Klaim",
                pesan=f"Klaim masuk untuk Laporan ID {klm.laporan_id}",
                waktu=klm.tanggal_klaim.isoformat(),
                status=klm.status_klaim.value
            ))
            
        # Urutkan secara python list (karena jumlah maksimal hanya 10 item)
        activities.sort(key=lambda x: x.waktu, reverse=True)
        recent_activities = activities[:5] # Kembalikan 5 paling baru secara absolut
        
        return DashboardStatsResponse(
            total_laporan=total_laporan,
            total_diverifikasi=total_diverifikasi,
            total_pending=total_pending,
            total_klaim_masuk=total_klaim_masuk,
            distribusi_kategori=distribusi_kategori,
            traffic_laporan=traffic_laporan,
            recent_activities=recent_activities
        )
