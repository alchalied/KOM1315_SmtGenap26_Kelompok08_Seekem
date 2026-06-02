from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.cores.database import get_db
from app.models.user import User
from app.models.laporan import Laporan
from app.api.deps import get_current_user
from app.services.notifikasi_service import NotifikasiService
from app.models.notifikasi import TipeNotifikasi
from app.schemas.contact import ContactReporterRequest
from app.services.email_service import EmailService

# Menggunakan prefix kosong karena router akan di-mount di /api/laporan oleh main.py
router = APIRouter()

@router.post("/{item_id}/hubungi")
async def send_message(
    item_id: int,
    body: ContactReporterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint untuk fitur 'Hubungi Pelapor'.
    Menerima whatsapp dan pesan, lalu mengirim email ke pelapor asli.
    """
    lap = db.query(Laporan).filter(Laporan.id == item_id).first()
    if not lap:
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan")
    
    if lap.pelapor_id == current_user.id:
        raise HTTPException(status_code=400, detail="Anda tidak dapat mengirim pesan ke laporan Anda sendiri")

    # Pastikan relasi pelapor termuat
    target_user = lap.pelapor
    if not target_user:
        raise HTTPException(status_code=500, detail="Data pelapor asli tidak ditemukan di sistem")

    target_email = target_user.email
    reporter_name = target_user.name
    item_name = lap.nama_barang
    sender_name = current_user.name
    sender_whatsapp = body.whatsapp
    message_content = body.pesan
    # Kirim parameter jenis laporan agar copy emailnya tepat
    item_type = lap.jenis_laporan.value

    # Kirim email menggunakan BackgroundTasks agar response API tidak memblokir (non-blocking)
    background_tasks.add_task(
        EmailService.send_contact_email,
        target_email=target_email,
        reporter_name=reporter_name,
        item_name=item_name,
        sender_name=sender_name,
        sender_whatsapp=sender_whatsapp,
        message=message_content,
        item_type=item_type
    )

    # Tetap kirim notifikasi in-app
    pesan_notif = f"{current_user.name} ingin menghubungi Anda terkait {lap.nama_barang}. Cek Email Anda."
    NotifikasiService.create_notifikasi(
        db=db,
        user_id=lap.pelapor_id,
        pesan=pesan_notif[:255],
        tipe=TipeNotifikasi.INFO
    )
    db.commit()

    return {"status": "success", "message": "Email berhasil dikirim ke pelapor"}
