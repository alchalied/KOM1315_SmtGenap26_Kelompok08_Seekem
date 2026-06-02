from sqlalchemy.orm import Session
from app.models.notifikasi import Notifikasi, TipeNotifikasi

class NotifikasiService:
    @staticmethod
    def create_notifikasi(db: Session, user_id: int, pesan: str, tipe: TipeNotifikasi) -> Notifikasi:
        new_notif = Notifikasi(
            user_id=user_id,
            pesan=pesan,
            tipe=tipe
        )
        db.add(new_notif)
        return new_notif
