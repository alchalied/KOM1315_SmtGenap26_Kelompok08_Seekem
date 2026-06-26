# 05 Testing Logs - SEEKEM

Folder ini berisi bukti pengujian keamanan (security unit testing) untuk implementasi protokol keamanan AAA (Authentication, Authorization, Accounting) dan kriptografi pada sistem SEEKEM (Sistem Elektronik Etalase Kehilangan & Penemuan).

## Bukti Pengujian Keamanan yang Diharapkan (Ketentuan Tugas)
Sesuai dengan ketentuan tugas keamanan informasi, mahasiswa wajib mengunggah hasil unit testing untuk fungsi-fungsi keamanan. Di antaranya:
- **Authentication**: Pengujian kekuatan sandi melalui hashing & salting (`bcrypt`), verifikasi JWT, serta penolakan akses jika token tidak valid/tidak ada.
- **Authorization**: Log yang menunjukkan bahwa user tanpa hak akses (tanpa token Authorization) gagal mengakses data terenkripsi atau endpoint sensitif admin (`401 Unauthorized` / `403 Forbidden`).
- **Accounting & Non-Repudiation**: Pengujian pembuatan tanda tangan digital (`Ed25519`) pada entri audit log dan pembuktian bahwa jika data audit log dimanipulasi (tampered), tanda tangan tersebut otomatis menjadi tidak valid.
- **Data Encryption**: Pembuktian bahwa data pribadi sensitif (seperti nomor telepon pengguna) disimpan dalam bentuk terenkripsi (*encryption-at-rest*) di database menggunakan AES-GCM dan didekripsi kembali hanya untuk pengguna yang berhak.

## Daftar Berkas Hasil Pengujian
Berikut adalah laporan rinci hasil pengujian unit keamanan sistem SEEKEM:
1. **[Security Test Log](security_test_log.md)**: Menyajikan skenario pengujian, tabel status kelulusan (PASSED), potongan kode bukti implementasi, serta log mentah hasil eksekusi unit test.
