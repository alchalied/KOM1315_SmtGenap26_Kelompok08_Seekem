from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.cores.database import SessionLocal  # noqa: E402
from app.models import activity_log, audit_log, klaim, laporan, notifikasi, user  # noqa: F401,E402
from app.models.audit_log import AuditLog  # noqa: E402
from app.utils.audit_signature import AUDIT_SIGNATURE_ALGORITHM, sign_audit_log  # noqa: E402


def sign_existing_logs() -> None:
    db = SessionLocal()
    signed_count = 0

    try:
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.signature.is_(None))
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
            .all()
        )

        for log in logs:
            signature = sign_audit_log(log)
            if signature is None:
                raise RuntimeError("AUDIT_SIGNATURE_PRIVATE_KEY is required to sign audit logs.")

            log.signature_algorithm = AUDIT_SIGNATURE_ALGORITHM
            log.signature = signature
            signed_count += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"audit_logs: signed {signed_count} unsigned row(s)")


if __name__ == "__main__":
    sign_existing_logs()
