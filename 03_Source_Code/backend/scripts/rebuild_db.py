from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.cores.config import settings  # noqa: E402


POSTGRES_ENUM_TYPES = (
    "userrole",
    "jenislaporan",
    "statuslaporan",
    "statusklaim",
    "tipenotifikasi",
)


def _redacted_database_url() -> str:
    url = make_url(settings.DATABASE_URL)
    return str(url.set(password="***") if url.password else url)


def _is_local_database_url() -> bool:
    url = make_url(settings.DATABASE_URL)

    if url.drivername.startswith("sqlite"):
        return True

    local_hosts = {None, "", "localhost", "127.0.0.1", "::1"}
    return url.host in local_hosts


def _assert_development_target(allow_non_local: bool) -> None:
    if allow_non_local or _is_local_database_url():
        return

    raise RuntimeError(
        "Refusing to rebuild a non-local database. "
        "Set DATABASE_URL to a local development database, or pass "
        "--allow-non-local only if you fully understand the risk."
    )


def _alembic_config():
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return config


def validate_runtime_requirements(stamp_alembic: bool, audit: bool) -> None:
    missing: list[str] = []

    if stamp_alembic:
        try:
            import alembic  # noqa: F401
        except ModuleNotFoundError:
            missing.append("alembic")

    if audit:
        try:
            import sqlalchemy  # noqa: F401
        except ModuleNotFoundError:
            missing.append("SQLAlchemy")

    if missing:
        packages = ", ".join(sorted(set(missing)))
        raise RuntimeError(
            f"Missing Python package(s): {packages}. "
            "Install backend dependencies first with: pip install -r requirements.txt"
        )


def rebuild_database() -> None:
    from app.cores.database import engine
    from app.models.base import Base

    # Import all models so SQLAlchemy registers every table in Base.metadata.
    from app.models import activity_log, audit_log, klaim, laporan, notifikasi, user  # noqa: F401

    with engine.begin() as connection:
        Base.metadata.drop_all(bind=connection)

        if engine.dialect.name == "postgresql":
            for enum_type in POSTGRES_ENUM_TYPES:
                connection.exec_driver_sql(f'DROP TYPE IF EXISTS "{enum_type}" CASCADE')

        Base.metadata.create_all(bind=connection)


def stamp_alembic_head() -> None:
    from alembic import command

    command.stamp(_alembic_config(), "head", purge=True)


def audit_schema() -> bool:
    from sqlalchemy import inspect

    from app.cores.database import engine
    from app.models.base import Base

    # Import all models so SQLAlchemy registers every table in Base.metadata.
    from app.models import activity_log, audit_log, klaim, laporan, notifikasi, user  # noqa: F401

    inspector = inspect(engine)
    database_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables)

    ok = True
    missing_tables = sorted(model_tables - database_tables)
    if missing_tables:
        ok = False
        print("Missing tables:", ", ".join(missing_tables))

    for table_name, table in Base.metadata.tables.items():
        if table_name not in database_tables:
            continue

        database_columns = {column["name"] for column in inspector.get_columns(table_name)}
        model_columns = set(table.columns.keys())

        missing_columns = sorted(model_columns - database_columns)
        extra_columns = sorted(database_columns - model_columns)

        if missing_columns:
            ok = False
            print(f"Missing columns in {table_name}: {', '.join(missing_columns)}")
        if extra_columns:
            ok = False
            print(f"Extra columns in {table_name}: {', '.join(extra_columns)}")

    if "alembic_version" in database_tables:
        with engine.connect() as connection:
            rows = connection.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).fetchall()
        versions = ", ".join(row[0] for row in rows) or "(empty)"
        print(f"Alembic version: {versions}")
    else:
        ok = False
        print("Missing table: alembic_version")

    if ok:
        print("Schema audit passed: database tables match SQLAlchemy models.")

    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Drop semua tabel aplikasi lalu buat ulang dari SQLAlchemy models "
            "untuk database development lokal."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Konfirmasi bahwa semua data pada tabel aplikasi boleh dihapus.",
    )
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help="Izinkan target DATABASE_URL non-lokal. Jangan gunakan untuk production.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tampilkan target database tanpa menghapus atau membuat tabel.",
    )
    parser.add_argument(
        "--no-stamp",
        action="store_true",
        help="Jangan stamp alembic_version ke revision head setelah rebuild.",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Lewati audit schema setelah rebuild.",
    )
    args = parser.parse_args()

    _assert_development_target(args.allow_non_local)

    if args.dry_run:
        print(f"Database target: {_redacted_database_url()}")
        print("Dry run only. No tables were dropped or created.")
        return

    if not args.yes:
        print("Perintah ini akan menghapus semua data tabel aplikasi.")
        print(f"Database target: {_redacted_database_url()}")
        print("Jalankan ulang dengan --yes jika sudah yakin.")
        raise SystemExit(1)

    validate_runtime_requirements(
        stamp_alembic=not args.no_stamp,
        audit=not args.skip_audit,
    )

    print(f"Rebuilding database: {_redacted_database_url()}")
    rebuild_database()
    print("Database berhasil dibuat ulang dari SQLAlchemy models.")

    if not args.no_stamp:
        stamp_alembic_head()
        print("Alembic version stamped to head.")

    if not args.skip_audit and not audit_schema():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
