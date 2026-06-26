import os
import sys
from pathlib import Path

# Add project root and backend to sys.path so sibling directories can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT))

import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import FastAPI application
from app.main import app

# Import dependencies and database access
from database.database import get_db
from database.encryption import encrypt_text, decrypt_text, ENCRYPTED_PREFIX
from digital_signature.audit_signature import sign_audit_log, verify_audit_log_signature, AUDIT_SIGNATURE_ALGORITHM
from src.auth.security import get_password_hash, create_access_token
from app.models.base import Base
from app.models import user, laporan, klaim, notifikasi, audit_log, activity_log
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog


TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"
# Clean up old test DB if it exists
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

# Create an SQLite database file for isolated unit testing
engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database tables
Base.metadata.create_all(bind=engine)


# FastAPI dependency override function
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency in the FastAPI application
app.dependency_overrides[get_db] = override_get_db


class SecurityTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup test database content
        cls.db = TestingSessionLocal()

        # Create password hashes
        admin_pass = get_password_hash("AdminSecur3!")
        user_pass = get_password_hash("UserSecur3!")

        # 1. Create test users
        cls.admin_user = User(
            name="Admin Tester",
            email="admin@seekem.local",
            nim="123456",
            phone="+628111111111", # Sensitive, will be encrypted automatically
            password_hash=admin_pass,
            role=UserRole.admin,
            is_verified=True
        )

        cls.normal_user = User(
            name="Regular Tester",
            email="user@seekem.local",
            nim="654321",
            phone="+628999999999", # Sensitive, will be encrypted automatically
            password_hash=user_pass,
            role=UserRole.civitas,
            is_verified=True
        )

        cls.db.add(cls.admin_user)
        cls.db.add(cls.normal_user)
        cls.db.commit()
        cls.db.refresh(cls.admin_user)
        cls.db.refresh(cls.normal_user)

        # Generate JWT tokens for testing
        cls.admin_token = create_access_token({"sub": cls.admin_user.email})
        cls.user_token = create_access_token({"sub": cls.normal_user.email})

        # Client for HTTP requests
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        
        # Clean up database file after test suite finishes
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass

    # ════════════════════════════════════════════════
    # 1. DATA ENCRYPTION TESTS (Fungsi Keamanan: Data Encryption)
    # ════════════════════════════════════════════════

    def test_01_encryption_decryption_utility(self):
        """Uji fungsi enkripsi dan dekripsi langsung."""
        plaintext = "Nomor Telepon Rahasia 0812345"
        encrypted = encrypt_text(plaintext)
        
        # Harus diawali dengan prefix enkripsi
        self.assertTrue(encrypted.startswith(ENCRYPTED_PREFIX))
        self.assertNotEqual(plaintext, encrypted)
        
        # Harus dapat didekripsi kembali
        decrypted = decrypt_text(encrypted)
        self.assertEqual(plaintext, decrypted)

    def test_02_database_encryption_at_rest(self):
        """Uji enkripsi data sensitif (at rest) di tingkat database."""
        # Query langsung menggunakan RAW SQL bypass ORM TypeDecorator
        with engine.connect() as conn:
            raw_result = conn.execute(text("SELECT phone FROM users WHERE email = :email"), {"email": "user@seekem.local"}).fetchone()
        db_stored_phone = raw_result[0]
        
        print(f"\n[DEBUG] Plaintext input: +628999999999")
        print(f"[DEBUG] Stored in database: {db_stored_phone}")

        # Assert bahwa data tersimpan dalam keadaan terenkripsi (memiliki prefix enc:v1:)
        self.assertTrue(db_stored_phone.startswith(ENCRYPTED_PREFIX))
        self.assertNotIn("+628999999999", db_stored_phone)

        # Query menggunakan SQLAlchemy ORM (Dekripsi otomatis melalui TypeDecorator)
        user = self.db.query(User).filter(User.email == "user@seekem.local").first()
        self.assertEqual(user.phone, "+628999999999")

    # ════════════════════════════════════════════════
    # 2. ACCESS CONTROL & AUTHORIZATION TESTS (Fungsi Keamanan: Authorization)
    # ════════════════════════════════════════════════

    def test_03_unauthorized_access_blocked(self):
        """Uji bahwa user tanpa token (Authorization) ditolak mengakses endpoint terproteksi."""
        response = self.client.get("/api/admin/verification")
        
        # Status code harus 401 Unauthorized karena tidak ada token
        self.assertEqual(response.status_code, 401)
        self.assertIn("Could not validate credentials", response.json()["detail"])
        print(f"\n[TEST LOG] Non-authorized user request to '/api/admin/verification' successfully BLOCKED with status {response.status_code}")

    def test_04_forbidden_access_blocked(self):
        """Uji bahwa user tanpa hak akses admin (role civitas) ditolak mengakses endpoint admin."""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = self.client.get("/api/admin/verification", headers=headers)
        
        # Status code harus 403 Forbidden karena user adalah 'civitas', bukan 'admin'
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Not enough permissions")
        print(f"[TEST LOG] Civitas role user request to '/api/admin/verification' successfully BLOCKED with status {response.status_code}")

    def test_05_authorized_access_allowed(self):
        """Uji bahwa user dengan hak akses yang tepat (admin) berhasil mengakses endpoint admin."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.get("/api/admin/verification", headers=headers)
        
        # Harus berhasil (200 OK)
        self.assertEqual(response.status_code, 200)
        print(f"[TEST LOG] Admin authorized request to '/api/admin/verification' ALLOWED with status {response.status_code}")

    # ════════════════════════════════════════════════
    # 3. DIGITAL SIGNATURE INTEGRITY TESTS (Fungsi Keamanan: Non-Repudiation)
    # ════════════════════════════════════════════════

    def test_06_digital_signature_tamper_detection(self):
        """Uji integritas data dan non-repudiation audit log."""
        # 1. Create a dummy AuditLog
        log = AuditLog(
            action="item.delete",
            actor_user_id=2,
            actor_email="user@seekem.local",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            success=True,
            resource_type="item",
            resource_id="99",
            detail="User deleted item with ID 99"
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        # 2. Sign the log entry
        signature = sign_audit_log(log)
        self.assertIsNotNone(signature)
        log.signature_algorithm = AUDIT_SIGNATURE_ALGORITHM
        log.signature = signature
        self.db.commit()
        self.db.refresh(log)

        # 3. Verifikasi signature awal (Harus valid)
        is_valid = verify_audit_log_signature(log)
        self.assertTrue(is_valid)
        print(f"\n[TEST LOG] Audit log signed. Verification status: {is_valid}")

        # 4. Tamper/Manipulasi data audit log (mengubah detail transaksi)
        log.detail = "User deleted item with ID 100"  # Diubah secara ilegal oleh penyerang
        self.db.commit()
        self.db.refresh(log)

        # 5. Verifikasi ulang signature setelah manipulasi (Harus tidak valid)
        is_valid_after_tamper = verify_audit_log_signature(log)
        self.assertFalse(is_valid_after_tamper)
        print(f"[TEST LOG] Audit log data TAMPERED. Verification status: {is_valid_after_tamper} (Tamper Detected successfully!)")


if __name__ == "__main__":
    unittest.main()
