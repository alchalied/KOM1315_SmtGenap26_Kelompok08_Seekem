from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.cores.database import get_db
from app.models.user import User
from app.models.notifikasi import Notifikasi
from app.schemas.notifikasi import NotifikasiResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[NotifikasiResponse])
def get_my_notifikasi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan daftar notifikasi khusus untuk user yang sedang login.
    Dilarang diakses oleh publik tanpa JWT.
    """
    notifikasis = db.query(Notifikasi)\
        .filter(Notifikasi.user_id == current_user.id)\
        .order_by(Notifikasi.tanggal_kirim.desc())\
        .all()
    return notifikasis

@router.patch("/read-all")
def mark_all_notifikasi_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menandai seluruh notifikasi milik current_user sebagai telah dibaca secara efisien.
    """
    db.query(Notifikasi)\
        .filter(Notifikasi.user_id == current_user.id)\
        .filter(Notifikasi.is_read == False)\
        .update({"is_read": True})
        
    db.commit()
    
    return {"status": "success", "message": "Semua notifikasi ditandai sudah dibaca"}

@router.patch("/{notifikasi_id}/read")
def mark_notifikasi_as_read(
    notifikasi_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menandai sebuah notifikasi telah dibaca.
    Hanya bisa dilakukan jika notifikasi tersebut milik current_user.
    """
    notif = db.query(Notifikasi)\
        .filter(Notifikasi.id == notifikasi_id)\
        .filter(Notifikasi.user_id == current_user.id)\
        .first()
        
    if not notif:
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan atau bukan milik Anda")
        
    notif.is_read = True
    db.commit()
    
    return {"status": "success", "message": "Notifikasi ditandai sudah dibaca"}
