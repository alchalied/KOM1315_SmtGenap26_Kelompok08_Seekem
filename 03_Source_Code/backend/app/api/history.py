from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

from app.cores.database import get_db
from app.models.user import User
from app.models.laporan import Laporan, StatusLaporan
from app.models.klaim import Klaim
from app.api.deps import get_current_user
from app.api.items import _laporan_to_item
from app.api.admin import _klaim_to_admin_claim

router = APIRouter()

@router.get("", response_model=Any)
def get_user_history(
    userId: int = None,
    nim: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mendapatkan riwayat laporan dan klaim milik user.
    """
    # Gunakan current_user.id sebagai default jika userId tidak dikirim
    target_id = userId if userId else current_user.id
    target_nim = nim if nim else current_user.nim

    # Ambil Laporan
    laporans = db.query(Laporan).filter(Laporan.pelapor_id == target_id).all()
    reports_res = []
    for lap in laporans:
        item_res = _laporan_to_item(lap)
        item_dict = item_res
        item_dict["itemId"] = item_dict["id"]
        
        # Override status to verification status so History FE can map it
        if lap.status.value == "pending":
            item_dict["status"] = "pending_verification"
        elif lap.status.value == "published":
            item_dict["status"] = "verified"
        else:
            item_dict["status"] = lap.status.value
            
        reports_res.append(item_dict)

    # Ambil Klaim
    klaims = db.query(Klaim).filter(
        (Klaim.pengklaim_id == target_id) | (Klaim.nim == target_nim)
    ).all()
    claims_res = [_klaim_to_admin_claim(k) for k in klaims]

    return {
        "reports": reports_res,
        "claims": claims_res
    }
