from fastapi import APIRouter, Depends, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List

from app.cores.database import get_db
from app.models.user import User
from app.schemas.klaim import KlaimCreate, KlaimResponse, KlaimVerify
from app.services.klaim_service import KlaimService
from app.services.upload_service import UploadService
from app.api.deps import get_current_user, get_current_active_admin

router = APIRouter()

@router.post("/", response_model=KlaimResponse, status_code=status.HTTP_201_CREATED)
async def create_klaim(
    laporan_id: int = Form(...),
    alasan_klaim: str = Form(...),
    bukti_foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User (civitas) membuat klaim atas suatu laporan. 
    Menerima file gambar bukti via `multipart/form-data`.
    """
    # 1. Unggah bukti gambar
    foto_url = await UploadService.upload_image(bukti_foto)
    
    # 2. Susun payload
    klaim_in = KlaimCreate(
        laporan_id=laporan_id,
        alasan_klaim=alasan_klaim,
        bukti_foto_url=foto_url
    )
    
    return KlaimService.create_klaim(db=db, klaim_in=klaim_in, pengklaim_id=current_user.id)

@router.get("/admin/pending", response_model=List[KlaimResponse])
def get_pending_klaims(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Admin mengecek daftar klaim yang masuk dan butuh verifikasi.
    """
    return KlaimService.get_pending_klaims(db, skip=skip, limit=limit)

@router.patch("/{klaim_id}/verify", response_model=KlaimResponse)
def verify_klaim(
    klaim_id: int,
    klaim_verify: KlaimVerify,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Admin menyetujui (Approve) atau menolak (Reject) klaim.
    Jika di-reject, Laporan akan kembali berstatus 'published'.
    """
    return KlaimService.verify_klaim(db=db, klaim_id=klaim_id, is_approved=klaim_verify.is_approved)
