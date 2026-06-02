from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.laporan import Laporan, StatusLaporan, JenisLaporan
from app.schemas.laporan import LaporanCreate
from sqlalchemy import or_

class LaporanService:
    
    @staticmethod
    def create_laporan(db: Session, laporan_in: LaporanCreate, pelapor_id: int) -> Laporan:
        new_laporan = Laporan(
            **laporan_in.dict(),
            pelapor_id=pelapor_id,
            status=StatusLaporan.pending
        )
        db.add(new_laporan)
        db.commit()
        db.refresh(new_laporan)
        return new_laporan

    @staticmethod
    def search_laporans(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: StatusLaporan = None,
        jenis: JenisLaporan = None,
        kategori: str = None,
        search_query: str = None
    ) -> list[Laporan]:
        query = db.query(Laporan)
        
        if status:
            query = query.filter(Laporan.status == status)
        if jenis:
            query = query.filter(Laporan.jenis_laporan == jenis)
        if kategori:
            query = query.filter(Laporan.kategori.ilike(f"%{kategori}%"))
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    Laporan.nama_barang.ilike(search_term),
                    Laporan.deskripsi.ilike(search_term)
                )
            )
            
        return query.order_by(Laporan.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_laporan_status(db: Session, laporan_id: int, new_status: StatusLaporan) -> Laporan:
        laporan = db.query(Laporan).filter(Laporan.id == laporan_id).first()
        if laporan:
            laporan.status = new_status
            db.commit()
            db.refresh(laporan)
        return laporan
        
    @staticmethod
    def get_laporan_by_id(db: Session, laporan_id: int) -> Laporan:
        laporan = db.query(Laporan).filter(Laporan.id == laporan_id).first()
        if not laporan:
            raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
        return laporan

    @staticmethod
    def resolve_laporan_by_owner(db: Session, laporan_id: int, user_id: int) -> Laporan:
        laporan = db.query(Laporan).filter(Laporan.id == laporan_id).first()
        if not laporan:
            raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
        
        if laporan.pelapor_id != user_id:
            raise HTTPException(status_code=403, detail="Anda bukan pemilik laporan ini")
            
        laporan.status = StatusLaporan.resolved
        db.commit()
        db.refresh(laporan)
        return laporan
