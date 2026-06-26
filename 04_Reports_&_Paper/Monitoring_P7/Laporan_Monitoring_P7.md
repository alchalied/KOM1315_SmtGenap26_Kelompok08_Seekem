# Laporan Monitoring P7

## Proyek PBL Keamanan Informasi KOM1315

**Nama sistem:** SEEKEM (Sistem Elektronik Etalase Kehilangan & Penemuan)
**Kelompok:** Kelompok 8
**Semester:** Genap 2025/2026
**Tahap:** Monitoring Pertemuan/Minggu ke-7
**Tanggal penyusunan:** 26 Juni 2026

## Ringkasan Eksekutif

Laporan Monitoring P7 ini disusun sebagai bukti kemajuan proyek SEEKEM sampai minggu ke-7 sesuai instruksi pengelolaan repositori Git untuk mata kuliah KOM1315 Keamanan Informasi. Pada tahap ini, kelompok telah menyelesaikan baseline analisis sistem, threat modeling, dan rancangan awal integrasi keamanan.

Sampai minggu ke-7, implementasi keamanan yang sudah berjalan pada sistem utama adalah **Authentication** dan **Authorization**. Authentication telah diarahkan untuk mendukung registrasi, login, penyimpanan password secara aman menggunakan bcrypt, verifikasi email, serta penerbitan dan validasi JSON Web Token (JWT). Authorization telah diarahkan untuk membatasi akses berdasarkan peran pengguna (admin dan civitas) serta kepemilikan data (ownership check). Kedua kontrol tersebut tidak dibuat sebagai skrip terpisah, tetapi langsung diintegrasikan ke workflow utama aplikasi SEEKEM.

Komponen **Accounting** atau audit logging sudah mulai diimplementasikan pada minggu ke-7. Setiap aksi krusial pada sistem telah tercatat ke dalam tabel `audit_logs` di database. Setiap entri audit log juga telah ditandatangani secara kriptografis menggunakan algoritma **Ed25519 Digital Signature** untuk menjamin integritas dan non-repudiation.

## Bab 1. Pendahuluan

### 1.1 Latar Belakang

SEEKEM adalah platform digital berbasis web yang dirancang untuk manajemen pelaporan barang hilang dan temuan di lingkup kampus IPB University. Dikembangkan dengan penekanan kuat pada aspek keamanan (*Security by Design*), inti dari arsitektur SEEKEM berpusat pada implementasi kerangka perlindungan **AAA (Authentication, Authorization, Accounting)**.

Karena SEEKEM menangani data pribadi civitas akademika seperti nama, NIM, nomor telepon, email, serta bukti-bukti klaim, sistem membutuhkan kontrol keamanan yang jelas. Risiko utama pada sistem seperti ini meliputi pencurian akun, akses tidak sah ke data sensitif, manipulasi status laporan dan klaim, kebocoran informasi kontak pribadi, dan tidak adanya bukti aktivitas ketika terjadi insiden.

Monitoring P7 difokuskan pada evaluasi progres awal proyek, terutama hasil analisis, rancangan keamanan, dan implementasi awal yang sudah terintegrasi ke sistem.

### 1.2 Tujuan Laporan

Tujuan laporan Monitoring P7 adalah:

- Menjelaskan kondisi dan kebutuhan keamanan SEEKEM sampai minggu ke-7.
- Merangkum hasil analisis sistem dan ancaman utama.
- Mendokumentasikan progres implementasi Authentication dan Authorization.
- Mendokumentasikan progres awal implementasi Accounting (audit logging dengan digital signature).
- Menjadi baseline sebelum pengembangan keamanan lanjutan pada minggu berikutnya.

### 1.3 Ruang Lingkup

Ruang lingkup monitoring mencakup:

- Analisis kebutuhan keamanan sistem SEEKEM.
- Threat modeling untuk aktor civitas, admin, dan pengguna tidak sah.
- Progres integrasi Authentication ke backend dan frontend.
- Progres integrasi Authorization berbasis role dan ownership.
- Progres awal Accounting berupa audit logging dengan tanda tangan digital Ed25519.
- Rencana lanjutan untuk enkripsi data sensitif dan pengujian end-to-end.

Ruang lingkup ini belum mencakup implementasi lengkap enkripsi field-level untuk seluruh data sensitif, maupun log pengujian end-to-end yang komprehensif.

## Bab 2. Analisis Sistem dan Risiko

### 2.1 Ringkasan Sistem

SEEKEM memiliki dua aktor utama:

| Aktor             | Peran dalam sistem                                                                                               | Data atau fitur yang perlu dilindungi                                                            |
| ----------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Civitas akademika | Melaporkan barang hilang/temuan, mencari barang di etalase, mengajukan klaim, dan mengonfirmasi barang ditemukan | Profil pribadi (nama, NIM, email, nomor telepon), data laporan, riwayat klaim, bukti kepemilikan |
| Admin platform    | Memverifikasi laporan masuk, menyetujui atau menolak klaim, dan mengelola item yang dipublikasikan               | Data seluruh pengguna, data laporan, data klaim, log audit aktivitas sistem                      |

Alur utama sistem dimulai dari pengguna yang mengakses frontend (React/Vite), mengirim request ke backend API (FastAPI), lalu backend melakukan validasi dan mengambil atau memperbarui data pada database PostgreSQL. Berdasarkan analisis awal, titik kontrol keamanan utama berada pada proses registrasi, login, validasi token JWT, pengecekan role, pengecekan ownership, pencatatan audit, dan perlindungan data sensitif.

### 2.2 Aset yang Dilindungi

Aset penting yang diidentifikasi pada tahap analisis meliputi:

- Akun pengguna, termasuk email, password hash, dan role (admin/civitas).
- Profil civitas, termasuk nama, NIM, dan nomor telepon (dienkripsi di database).
- Data laporan barang hilang dan temuan beserta foto dokumentasi.
- Data klaim beserta bukti kepemilikan dan informasi kontak pengklaim (dienkripsi di database).
- Konfigurasi keamanan seperti `JWT_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, dan `AUDIT_SIGNATURE_PRIVATE_KEY`.
- Bukti aktivitas pengguna yang dicatat melalui audit log beserta tanda tangan digital.

### 2.3 Risiko Utama

Hasil threat modeling menunjukkan beberapa risiko prioritas:

| Risiko                           | Dampak                                                                                  | Mitigasi yang direncanakan                                                       |
| -------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Authentication lemah             | Pengambilalihan akun pengguna                                                           | Password hashing bcrypt, validasi login, JWT, token expiration, verifikasi email |
| Endpoint tidak membatasi role    | Civitas dapat mengakses fitur admin atau sebaliknya                                     | Role-based access control (admin vs civitas)                                     |
| Tidak ada ownership check        | Pengguna dapat mengklaim laporan miliknya sendiri atau mengonfirmasi laporan orang lain | Validasi kepemilikan data pada backend                                           |
| Password disimpan tidak aman     | Password dapat bocor jika database terekspos                                            | Hashing menggunakan bcrypt dengan auto-generated salt                            |
| Data kontak tersimpan plaintext  | Nomor telepon dan kontak bocor jika database terekspos                                  | Enkripsi field-level menggunakan AES-GCM                                         |
| Aktivitas penting tidak tercatat | Investigasi insiden sulit dilakukan                                                     | Audit logging ke tabel database dengan digital signature                         |
| Audit log dimanipulasi           | Bukti aktivitas kehilangan integritas                                                   | Tanda tangan digital Ed25519 pada setiap entri audit log                         |

### 2.4 Prioritas Keamanan

Berdasarkan risiko tersebut, prioritas keamanan sampai minggu ke-7 diarahkan pada tiga fondasi utama:

1. **Authentication**, agar sistem dapat memastikan identitas pengguna sebelum memberikan akses.
2. **Authorization**, agar sistem dapat memastikan pengguna hanya mengakses fitur dan data sesuai perannya.
3. **Accounting**, agar setiap tindakan krusial tercatat secara transparan dan anti-manipulasi.

Ketiga fondasi AAA ini telah menjadi fokus implementasi minggu ke-7, dengan Authentication dan Authorization yang lebih matang dan Accounting yang sudah memiliki fondasi awal.

## Bab 3. Progres Implementasi Hingga Minggu ke-7

### 3.1 Status Umum Progres

Sampai minggu ke-7, kelompok telah menyelesaikan dokumen proposal teknis, threat modeling, rancangan awal keamanan, dan integrasi Authentication, Authorization, serta Accounting awal pada aplikasi. Implementasi dilakukan langsung pada alur utama aplikasi, bukan sebagai modul demonstrasi yang berdiri sendiri.

| Komponen AAA   | Status P7                        | Keterangan                                                                                                                                                                                                   |
| -------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Authentication | Sudah dilakukan dan terintegrasi | Register, login, password hashing bcrypt, JWT (HS256), verifikasi email, reset password, dan proteksi endpoint sudah diarahkan ke workflow utama                                                             |
| Authorization  | Sudah dilakukan dan terintegrasi | Pembatasan akses berdasarkan role (admin/civitas), ownership check, dan pembatasan aksi berdasarkan status laporan sudah diarahkan pada endpoint dan route penting                                           |
| Accounting     | Sudah dilakukan (fondasi awal)   | Audit logging ke tabel`audit_logs` di database, setiap entri ditandatangani dengan Ed25519 digital signature, mencakup event registrasi, login, verifikasi email, verifikasi laporan, dan verifikasi klaim |

### 3.2 Progres Authentication

Authentication sampai minggu ke-7 telah difokuskan pada validasi identitas pengguna. Implementasi yang sudah dilakukan meliputi:

- Registrasi pengguna dengan data akun (nama, email, NIM, nomor telepon, password) dan role default civitas.
- Login menggunakan email dan password.
- Penyimpanan password menggunakan hashing bcrypt dengan auto-generated salt.
- Penerbitan access token JWT (algoritma HS256) dengan masa berlaku 7 hari.
- Validasi token JWT untuk mengakses endpoint yang membutuhkan autentikasi melalui dependency `get_current_user`.
- Verifikasi email menggunakan token acak (`secrets.token_urlsafe(32)`) dengan masa berlaku 24 jam.
- Fitur kirim ulang verifikasi email dengan rate limiting (cooldown 60 detik).
- Reset password menggunakan token acak dengan masa berlaku 15 menit.
- Rate limiting in-memory untuk endpoint forgot-password dan resend-verification (maksimal 5 permintaan per jam).
- Integrasi token dari frontend ke request backend melalui header `Authorization: Bearer`.

Pada backend, Authentication terhubung dengan modul `src/auth/security.py` (hashing dan JWT), `src/auth/deps.py` (dependency injection untuk mengambil current user), dan `src/auth/auth.py` (route register, login, verify-email, forgot-password, reset-password). Pada frontend, Authentication terhubung dengan halaman login, halaman register, dan API client yang membawa token pada setiap request.

Dengan integrasi ini, pengguna tidak hanya diverifikasi pada tampilan frontend, tetapi juga pada backend. Hal ini penting karena backend tetap menjadi titik validasi utama dan tidak mempercayai role atau identitas hanya dari input client.

### 3.3 Progres Authorization

Authorization sampai minggu ke-7 telah difokuskan pada pembatasan akses berdasarkan role dan ownership. Role utama yang digunakan adalah:

- `civitas` untuk civitas akademika (pengguna umum).
- `admin` untuk pengelola platform.

Implementasi Authorization yang sudah dilakukan meliputi:

- Proteksi endpoint admin menggunakan dependency `get_current_active_admin` yang memeriksa `current_user.role.value == "admin"`.
- Pembatasan akses endpoint verifikasi laporan (`/api/admin/verification`), manajemen klaim (`/api/admin/claims`), manajemen item (`/api/admin/items`), dan audit log (`/api/admin/audit-logs`) hanya untuk role admin.
- Pembatasan bahwa admin tidak diperbolehkan membuat laporan barang (`report_item`) maupun mengajukan klaim (`create_claim`).
- Ownership check: hanya pelapor asli yang dapat mengonfirmasi bahwa laporannya sudah selesai (endpoint `confirm_lost_item_claimed`).
- Ownership check: pengguna tidak dapat mengklaim laporan miliknya sendiri.
- Pembatasan klaim hanya pada laporan yang berstatus `published` atau `resolved`.
- Pemisahan route dan dashboard berdasarkan role di frontend.

Contoh integrasi Authorization adalah civitas hanya dapat membuat laporan, mencari barang, dan mengajukan klaim, sedangkan admin memiliki akses untuk memverifikasi laporan, menyetujui atau menolak klaim, dan mengelola item yang sudah dipublikasikan. Setiap endpoint yang membutuhkan autentikasi menggunakan dependency `get_current_user`, dan endpoint admin tambahan menggunakan `get_current_active_admin`.

### 3.4 Status Accounting

Accounting telah diimplementasikan pada minggu ke-7 sebagai fondasi awal. Sistem sudah memiliki mekanisme audit trail yang mencatat aktivitas penting dan menandatanganinya secara kriptografis. Implementasi yang sudah dilakukan meliputi:

- Tabel `audit_logs` di database dengan kolom: `id`, `actor_user_id`, `actor_email`, `action`, `resource_type`, `resource_id`, `detail`, `ip_address`, `user_agent`, `success`, `created_at`, `signature_algorithm`, dan `signature`.
- Service `AuditLogService.create()` untuk mencatat setiap aksi ke tabel audit log.
- Tanda tangan digital Ed25519 pada setiap entri audit log melalui modul `digital_signature/audit_signature.py`.
- Verifikasi signature melalui property `signature_valid` pada model `AuditLog`.

Event yang sudah di-audit meliputi:

| Event                                  | Resource | Kapan                                                      |
| -------------------------------------- | -------- | ---------------------------------------------------------- |
| `auth.register`                      | user     | User baru mendaftar                                        |
| `auth.register.duplicate_email`      | —       | Registrasi dengan email duplikat                           |
| `auth.login.success`                 | user     | Login berhasil                                             |
| `auth.login.failed`                  | —       | Login gagal (password salah atau email belum diverifikasi) |
| `auth.email_verify.success`          | user     | Email berhasil diverifikasi                                |
| `auth.email_verify.failed`           | —       | Token verifikasi tidak valid atau kedaluwarsa              |
| `auth.verification_resend.requested` | —       | Permintaan kirim ulang verifikasi email                    |
| `auth.forgot_password.requested`     | —       | Permintaan reset password                                  |
| `auth.reset_password.success`        | user     | Password berhasil direset                                  |
| `auth.reset_password.failed`         | —       | Token reset password tidak valid atau kedaluwarsa          |
| `admin.report.approve`               | laporan  | Admin menyetujui laporan                                   |
| `admin.report.reject`                | laporan  | Admin menolak laporan                                      |
| `admin.claim.approve`                | klaim    | Admin menyetujui klaim                                     |
| `admin.claim.reject`                 | klaim    | Admin menolak klaim                                        |
| `admin.item.delete`                  | laporan  | Admin menghapus item                                       |
| `admin.item.hold`                    | laporan  | Admin menahan item                                         |
| `admin.item.post`                    | laporan  | Admin memublikasikan kembali item                          |
| `admin.item.cancel_claim`            | laporan  | Admin membatalkan klaim pada item                          |

## Kesimpulan

Sampai minggu ke-7, proyek SEEKEM telah memiliki baseline analisis dan rancangan keamanan yang memadai serta implementasi awal yang terintegrasi langsung ke sistem utama. Authentication mendukung validasi identitas pengguna melalui registrasi, login, hashing password bcrypt, JWT, verifikasi email, dan reset password. Authorization mendukung pembatasan akses berdasarkan role (admin/civitas) dan kepemilikan data. Accounting mendukung pencatatan audit trail dengan tanda tangan digital Ed25519 pada setiap entri.

Selain AAA, implementasi minggu ke-7 juga mencakup enkripsi field-level menggunakan AES-GCM untuk melindungi data sensitif (nomor telepon dan kontak) di database, serta digital signature menggunakan Ed25519 untuk menjamin integritas dan non-repudiation audit log. Test suite keamanan juga telah tersedia untuk memvalidasi fungsi enkripsi, access control, dan deteksi manipulasi data.

Fondasi keamanan ini menjadi titik awal yang solid untuk pengembangan lanjutan, termasuk perluasan cakupan audit, penguatan hash chain, dan pengujian end-to-end pada minggu-minggu berikutnya.
