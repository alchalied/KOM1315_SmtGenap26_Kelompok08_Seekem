from pathlib import Path
import sys

from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT))

from database.database import SessionLocal
from database.encryption import ENCRYPTED_PREFIX, encrypt_text


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
