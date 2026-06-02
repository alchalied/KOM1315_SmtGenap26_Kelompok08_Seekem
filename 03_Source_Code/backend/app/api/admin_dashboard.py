from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.cores.database import get_db
from app.models.user import User
from app.models.laporan import StatusLaporan
from app.models.klaim import StatusKlaim
from app.api.deps import get_current_active_admin
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.laporan import LaporanResponse
from app.schemas.klaim import KlaimResponse
from app.services.dashboard_service import DashboardService
from app.services.laporan_service import LaporanService
from app.services.klaim_service import KlaimService

router = APIRouter()

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Mengembalikan data statistik agregat untuk dashboard admin.
    Semua proses dihitung di database scale (count, group by).
    """
    return DashboardService.get_dashboard_stats(db)

@router.get("/laporan", response_model=List[LaporanResponse])
def get_dashboard_laporan(
    skip: int = 0, 
    limit: int = 20, 
    status: StatusLaporan = None,
    search: str = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Tabel manajemen laporan di dashboard admin.
    Terdapat paginasi untuk mencegah over-fetching.
    """
    return LaporanService.search_laporans(
        db, skip=skip, limit=limit, status=status, search_query=search
    )

@router.get("/klaim", response_model=List[KlaimResponse])
def get_dashboard_klaim(
    skip: int = 0, 
    limit: int = 20, 
    status: StatusKlaim = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Tabel manajemen klaim di dashboard admin.
    Terdapat paginasi untuk mencegah over-fetching.
    """
    return KlaimService.search_klaims(
        db, skip=skip, limit=limit, status_klaim=status
    )
