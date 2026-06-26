from pathlib import Path
import sys

from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.cores.database import SessionLocal
from app.utils.encryption import ENCRYPTED_PREFIX, encrypt_text


SENSITIVE_FIELDS = (
    ("users", "id", "phone"),
    ("klaim", "id", "contact"),
)


def encrypt_existing_plaintext() -> None:
    db = SessionLocal()
    encrypted_counts: dict[str, int] = {}

    try:
        for table_name, id_column, value_column in SENSITIVE_FIELDS:
            rows = db.execute(
                text(f'SELECT "{id_column}", "{value_column}" FROM "{table_name}"')
            ).fetchall()

            encrypted_count = 0
            for row_id, value in rows:
                if not value or str(value).startswith(ENCRYPTED_PREFIX):
                    continue

                db.execute(
                    text(
                        f'UPDATE "{table_name}" '
                        f'SET "{value_column}" = :encrypted_value '
                        f'WHERE "{id_column}" = :row_id'
                    ),
                    {
                        "encrypted_value": encrypt_text(str(value)),
                        "row_id": row_id,
                    },
                )
                encrypted_count += 1

            encrypted_counts[f"{table_name}.{value_column}"] = encrypted_count

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    for field_name, count in encrypted_counts.items():
        print(f"{field_name}: encrypted {count} plaintext row(s)")


if __name__ == "__main__":
    encrypt_existing_plaintext()
