from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from datetime import datetime

from app.cores.database import get_db
from app.models.user import User
from app.models.laporan import Laporan, StatusLaporan, JenisLaporan
from app.schemas.item import ItemResponse
from app.api.deps import get_current_user
from app.services.upload_service import UploadService

from app.models.klaim import Klaim, StatusKlaim
from app.models.notifikasi import TipeNotifikasi
from app.schemas.admin import AdminClaimResponse
from app.services.notifikasi_service import NotifikasiService
from app.api.admin import _klaim_to_admin_claim

router = APIRouter()


def _laporan_to_item(lap: Laporan) -> dict:
    """Memetakan model Laporan internal ke format ItemResponse yang diharapkan FE."""
    # FE menggunakan "lost" / "found" sebagai status, bukan status internal
    if lap.jenis_laporan == JenisLaporan.hilang:
        fe_status = "lost"
    else:
        fe_status = "found"
    
    # Format waktu ke string yang manusiawi
    time_str = ""
    if lap.tanggal_kejadian:
        time_str = lap.tanggal_kejadian.strftime("%d %b %Y, %H:%M")
    
    reporter_name = None
    if lap.pelapor:
        reporter_name = lap.pelapor.name

    fe_claim_status = None
    if lap.status.value == "resolved":
        fe_claim_status = "resolved"
    elif lap.status.value == "claimed":
        fe_claim_status = "claimed"

    return {
        "id": lap.id,
        "name": lap.nama_barang,
        "status": fe_status,
        "image": lap.foto_url,
        "location": lap.lokasi,
        "time": time_str,
        "category": lap.kategori,
        "description": lap.deskripsi,
        "reporterName": reporter_name,
        "reporterId": lap.pelapor_id,
        "tag": "Hilang" if lap.jenis_laporan == JenisLaporan.hilang else "Temuan",
        "reportTime": lap.created_at.strftime("%d %b %Y, %H:%M") if lap.created_at else None,
        "claimStatus": fe_claim_status,
    }


@router.get("", response_model=List[ItemResponse])
def get_items(
    type: str = "all",
    query: str = "",
    category: str = "",
    location: str = "",
    db: Session = Depends(get_db),
):
    """
    Endpoint publik /api/items yang digunakan FE.
    Params:
      - type: "all", "lost", "found"
      - query: pencarian teks
      - category: label kategori (string)
      - location: nama lokasi
    Hanya mengembalikan item yang sudah published.
    """
    q = db.query(Laporan).filter(
        Laporan.status == StatusLaporan.published
    )

    # Filter jenis laporan
    if type == "lost":
        q = q.filter(Laporan.jenis_laporan == JenisLaporan.hilang)
    elif type == "found":
        q = q.filter(Laporan.jenis_laporan == JenisLaporan.ditemukan)

    # Filter pencarian teks
    if query:
        search_term = f"%{query}%"
        q = q.filter(
            or_(
                Laporan.nama_barang.ilike(search_term),
                Laporan.deskripsi.ilike(search_term),
                Laporan.lokasi.ilike(search_term),
                Laporan.kategori.ilike(search_term),
            )
        )

    # Filter kategori
    if category:
        q = q.filter(Laporan.kategori.ilike(f"%{category}%"))

    # Filter lokasi
    if location:
        q = q.filter(Laporan.lokasi.ilike(f"%{location}%"))

    laporans = q.order_by(Laporan.created_at.desc()).limit(100).all()
    return [_laporan_to_item(lap) for lap in laporans]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    """
    Detail item berdasarkan ID. Digunakan oleh FE ItemDetail page.
    """
    lap = db.query(Laporan).filter(Laporan.id == item_id).first()
    if not lap:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    return _laporan_to_item(lap)


@router.post("/report/{type}", response_model=ItemResponse, status_code=201)
async def report_item(
    type: str,
    name: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    time: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Membuat laporan baru (menerima multipart/form-data).
    """
    if type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="Tipe laporan harus 'lost' atau 'found'")

    if current_user.role.value == "admin":
        raise HTTPException(status_code=403, detail="Admin tidak diperbolehkan membuat laporan barang.")

    jenis = JenisLaporan.hilang if type == "lost" else JenisLaporan.ditemukan

    try:
        tanggal = datetime.strptime(time, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        tanggal = datetime.utcnow()

    # Upload gambar ke layanan penyimpanan jika ada
    foto_url = None
    if image:
        foto_url = await UploadService.upload_image(image)

    new_lap = Laporan(
        pelapor_id=current_user.id,
        jenis_laporan=jenis,
        tanggal_kejadian=tanggal,
        lokasi=location,
        deskripsi=description,
        nama_barang=name,
        kategori=category,
        foto_url=foto_url,
        status=StatusLaporan.pending,
    )
    db.add(new_lap)
    db.commit()
    db.refresh(new_lap)
    return _laporan_to_item(new_lap)


@router.patch("/{item_id}/claim-confirmation", response_model=ItemResponse)
def confirm_lost_item_claimed(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FE memanggil: PATCH /api/items/{id}/claim-confirmation
    Digunakan ketika pelapor mengonfirmasi bahwa laporannya sudah selesai (ketemu/dikembalikan).
    """
    lap = db.query(Laporan).filter(Laporan.id == item_id).first()
    if not lap:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")

    if lap.pelapor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya pelapor yang dapat mengonfirmasi")

    if lap.status == StatusLaporan.resolved:
        raise HTTPException(status_code=400, detail="Barang sudah berstatus selesai")

    # Set status jadi resolved
    lap.status = StatusLaporan.resolved
    db.commit()
    db.refresh(lap)
    
    item = _laporan_to_item(lap)
    item["claimStatus"] = "claimed"
    item["claimantName"] = current_user.name
    item["claimedByReporter"] = True
    return item


@router.post("/{item_id}/claims", response_model=AdminClaimResponse, status_code=201)
async def create_claim(
    item_id: int,
    ownerName: str = Form(...),
    nim: str = Form(...),
    faculty: str = Form(""),
    contact: str = Form(""),
    description: str = Form(...),
    evidenceImage: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FE memanggil: POST /api/items/{item_id}/claims
    Menerima form data untuk membuat klaim barang.
    """
    if current_user.role.value == "admin":
        raise HTTPException(status_code=403, detail="Admin tidak diperbolehkan mengklaim barang.")

    # Cek apakah laporan ada
    lap = db.query(Laporan).filter(Laporan.id == item_id).first()
    if not lap:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    if lap.status not in (StatusLaporan.published, StatusLaporan.resolved):
        raise HTTPException(status_code=400, detail="Laporan ini tidak dapat diklaim saat ini")

    if lap.pelapor_id == current_user.id:
        raise HTTPException(status_code=400, detail="Anda tidak dapat mengklaim laporan Anda sendiri")

    try:
        # Unggah file ke Cloudinary
        foto_url = await UploadService.upload_image(evidenceImage)

        new_klaim = Klaim(
            laporan_id=item_id,
            pengklaim_id=current_user.id,
            alasan_klaim=description,
            bukti_foto_url=foto_url,
            owner_name=ownerName,
            nim=nim,
            faculty=faculty,
            contact=contact,
            status_klaim=StatusKlaim.pending,
        )
        db.add(new_klaim)

        # Update status laporan menjadi claimed
        lap.status = StatusLaporan.claimed

        # Notifikasi ke pemilik laporan
        NotifikasiService.create_notifikasi(
            db=db,
            user_id=lap.pelapor_id,
            pesan="Seseorang mengklaim barang Anda. Menunggu verifikasi Admin.",
            tipe=TipeNotifikasi.INFO,
        )

        db.commit()
        db.refresh(new_klaim)
        
        return _klaim_to_admin_claim(new_klaim)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal membuat klaim: {str(e)}")
