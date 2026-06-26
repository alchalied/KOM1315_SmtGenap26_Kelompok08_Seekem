# Security Test Log

Bukti pengujian fungsi-fungsi keamanan (*Authentication, Authorization, Accounting, Data Encryption, and Non-Repudiation*) pada sistem SEEKEM.

## Scenarios

| Skenario Pengujian                      | Hasil yang Diharapkan                                                                                                        | Status    | Bukti (Evidence)                                                                                                                                                        |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Encryption (at rest)**     | Data sensitif (nomor telepon pengguna) disimpan di database dalam bentuk ciphertext terenkripsi (diawali prefix`enc:v1:`). | ✅ PASSED | `test_02_database_encryption_at_rest` — Raw SQL select mengembalikan ciphertext, sedangkan SQLAlchemy ORM mendekripsinya secara otomatis.                            |
| **Data Decryption (utility)**     | Fungsi enkripsi dan dekripsi utilitas AES-GCM bekerja dua arah secara akurat.                                                | ✅ PASSED | `test_01_encryption_decryption_utility` — Hasil enkripsi berbeda dengan plaintext asli, dan dekripsi memulihkannya kembali.                                          |
| **Akses Tanpa Token Diblokir**    | Permintaan dari pengguna tanpa header`Authorization` ke endpoint terproteksi (`/api/admin/verification`) ditolak.        | ✅ PASSED | `test_03_unauthorized_access_blocked` — Mengembalikan HTTP status `401 Unauthorized` dengan pesan error validasi kredensial.                                       |
| **Akses Role Non-Admin Diblokir** | Pengguna dengan peran selain admin (`civitas`) ditolak saat mencoba mengakses endpoint administrasi.                       | ✅ PASSED | `test_04_forbidden_access_blocked` — Mengembalikan HTTP status `403 Forbidden` dengan pesan "Not enough permissions".                                              |
| **Akses Admin Diizinkan**         | Pengguna dengan peran`admin` yang sah berhasil mengakses endpoint administrasi.                                            | ✅ PASSED | `test_05_authorized_access_allowed` — Mengembalikan HTTP status `200 OK`.                                                                                          |
| **Deteksi Tamper Audit Log**      | Tanda tangan kriptografi (`Ed25519`) pada baris audit log mendeteksi adanya manipulasi atau perubahan data secara ilegal.  | ✅ PASSED | `test_06_digital_signature_tamper_detection` — Verifikasi tanda tangan bernilai `True` saat data asli, dan bernilai `False` setelah data audit log dimodifikasi. |

---

## 1. Bukti Enkripsi Data Sensitif (Data Encryption at Rest)

Sistem menggunakan enkripsi berbasis **AES-GCM (128-bit / 256-bit)** melalui decorator SQLAlchemy untuk melindungi data pribadi pengguna (NIM, Kontak Telepon, dll.) di database.

### Implementasi Kode

Di implementasikan pada berkas `database/encryption.py`:

```python
# database/encryption.py
class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_text(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return decrypt_text(value)
        return value
```

Di model `User` (`backend/app/models/user.py`):

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"
    ...
    phone = Column(EncryptedString(512), nullable=False)
```

### Bukti Pengujian Database

Saat data disimpan ke database, nomor telepon `+628999999999` terenkripsi secara otomatis:

```text
[DEBUG] Plaintext input: +628999999999
[DEBUG] Stored in database: enc:v1:FONqp3L4OQ4MKKfmQTw-IPkjnAAXJBSdRadkX7xcOrFgNJnyaGagCkc
```

* **Raw SQL Query** (`SELECT phone FROM users`) mengembalikan ciphertext aman dengan prefix `enc:v1:`.
* **SQLAlchemy Query** (`db.query(User)`) mengembalikan plaintext asli `+628999999999` secara transparan bagi sistem internal.

---

## 2. Bukti Kontrol Akses & Otorisasi (Authorization Access Control)

Setiap request ke route terproteksi divalidasi menggunakan token JWT Bearer melalui FastAPI Dependency Injection.

### Implementasi Kode

Pembatasan akses diatur pada berkas `src/auth/deps.py`:

```python
# src/auth/deps.py
def get_current_user(credentials = Depends(security), db: Session = Depends(get_db)):
    ...
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        ...
    except JWTError:
        raise credentials_exception

def get_current_active_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
```

### Bukti Log Blokir Akses

* **Tanpa Token**: Request diblokir dan mengembalikan status `401`.
  ```text
  [TEST LOG] Non-authorized user request to '/api/admin/verification' successfully BLOCKED with status 401
  ```
* **Akses Civitas (Role Biasa)**: Token valid tetapi tidak berhak mengakses panel admin, diblokir dengan status `403`.
  ```text
  [TEST LOG] Civitas role user request to '/api/admin/verification' successfully BLOCKED with status 403
  ```
* **Akses Admin (Role Sah)**: Diizinkan masuk dengan status `200`.
  ```text
  [TEST LOG] Admin authorized request to '/api/admin/verification' ALLOWED with status 200
  ```

---

## 3. Bukti Deteksi Manipulasi Audit Log (Digital Signature & Non-Repudiation)

Audit Log ditandatangani menggunakan kunci asimetris **Ed25519** untuk menjamin integritas riwayat transaksi sistem (akuntabilitas).

### Implementasi Kode

Di implementasikan pada berkas `digital_signature/audit_signature.py`:

```python
# digital_signature/audit_signature.py
def sign_audit_log(log) -> str | None:
    private_key = _private_key()
    if private_key is None:
        return None
    data = _canonical_log_representation(log)
    signature = private_key.sign(data)
    return _encode_base64url(signature)

def verify_audit_log_signature(log) -> bool:
    public_key = _public_key()
    if public_key is None:
        return False
    ...
    try:
        public_key.verify(signature, data)
        return True
    except Exception:
        return False
```

### Bukti Deteksi Modifikasi Data (Tampering)

Pengujian menyimulasikan adanya penyerang yang mengubah baris data audit secara ilegal di database:

```text
[TEST LOG] Audit log signed. Verification status: True
[TEST LOG] Audit log data TAMPERED. Verification status: False (Tamper Detected successfully!)
```

Tanda tangan kriptografis otomatis **gagal divalidasi** segera setelah data pada kolom `detail` diubah secara paksa, membuktikan ketahanan sistem dari repudiasi data.

---

## 4. Log Eksekusi Unit Testing (Raw Output)

Berikut adalah output mentah dari hasil eksekusi unit test `test_security.py`:

```text
D:\Data(S)\KULIAH\Semester 6\KI\Projek\KOM1315_SmtGenap26_Kelompok08_Seekem\03_Source_Code\src\auth\security.py:19: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
......
----------------------------------------------------------------------
Ran 6 tests in 0.511s

OK

[DEBUG] Plaintext input: +628999999999
[DEBUG] Stored in database: enc:v1:FONqp3L4OQ4MKKfmQTw-IPkjnAAXJBSdRadkX7xcOrFgNJnyaGagCkc

[TEST LOG] Non-authorized user request to '/api/admin/verification' successfully BLOCKED with status 401
[TEST LOG] Civitas role user request to '/api/admin/verification' successfully BLOCKED with status 403
[TEST LOG] Admin authorized request to '/api/admin/verification' ALLOWED with status 200

[TEST LOG] Audit log signed. Verification status: True
[TEST LOG] Audit log data TAMPERED. Verification status: False (Tamper Detected successfully!)
```

---

## Source & Lokasi Berkas Kode

- **Fitur Enkripsi**: 03_Source_Code/database/encryption.py)
- **Otorisasi & JWT**: 03_Source_Code/src/auth/security.py)
- **Tanda Tangan Digital**: 03_Source_Code/digital_signature/audit_signature.py)
- **Unit Test Script**: 03_Source_Code/backend/tests/test_security.py)
