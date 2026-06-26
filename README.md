# SEEKEM (Sistem Elektronik Etalase Kehilangan & Penemuan) - IPB University

## 1. Deskripsi Proyek
SEEKEM merupakan platform digital berbasis web yang berfokus pada manajemen pelaporan barang hilang dan temuan di lingkup kampus IPB University. Dikembangkan dengan penekanan kuat pada aspek keamanan (*Security by Design*), inti dari arsitektur SEEKEM berpusat pada implementasi kerangka perlindungan **AAA (*Authentication, Authorization, Accounting*)**.

Fokus implementasi modul keamanan pada sistem ini meliputi:
- **Autentikasi (*Authentication*)**: Mengamankan gerbang masuk sistem melalui verifikasi surel identitas (pembatasan *domain* institusi) dan perlindungan sesi komunikasi (*stateless*) berbasis *JSON Web Token* (JWT) tersandi.
- **Otorisasi (*Authorization*)**: Menerapkan kontrol akses berbasis peran (RBAC) yang memisahkan hak antara pengguna umum dan administrator. Sistem juga dilengkapi dengan proteksi *Mass Assignment* dan penyembunyian Informasi Identitas Pribadi (PII) hingga klaim tervalidasi.
- **Akuntabilitas (*Accounting*)**: Memastikan setiap tindakan krusial tercatat secara transparan dan anti-manipulasi (*tamper-proof*) dengan menerapkan *Cryptographic Signature* pada seluruh entri riwayat akses maupun pelacakan audit (*Audit Logs*).

### 1.1. Fitur Utama

- **Pelaporan Barang Terpusat**  
  Fasilitas bagi civitas akademika untuk melaporkan barang hilang maupun barang temuan secara terorganisir yang dilengkapi dengan fitur unggahan dokumentasi media pendukung.

- **Katalog Pencarian Terverifikasi**  
  Etalase penyajian daftar barang yang telah melalui tahap validasi oleh pengelola untuk memastikan keakuratan informasi saat diakses oleh publik.

- **Sistem Klaim Aman**  
  Penerapan prosedur keamanan terpadu yang mewajibkan pengguna untuk menyertakan bukti kepemilikan sah pada setiap langkah pengajuan klaim barang.

- **Perlindungan Privasi**  
  Penyembunyian informasi kontak pengguna menggunakan enkripsi tingkat basis data yang baru akan didistribusikan ke pihak terkait setelah klaim mendapat persetujuan pengelola.

- **Dasbor Administrator**  
  Antarmuka kendali operasional khusus bagi pengelola yang berfungsi untuk memverifikasi laporan masuk, menyetujui klaim, dan meninjau metrik aktivitas sistem harian.

- **Notifikasi Otomatis**  
  Layanan pemberitahuan seketika yang dikirimkan secara langsung melalui surel untuk memandu pengguna terkait status verifikasi akun, pemulihan sandi, maupun kemajuan proses klaim.

---

## 2. Panduan Instalasi (Lingkungan Pengembangan Lokal)

Bagian ini menguraikan tahapan teknis yang diperlukan untuk menginisialisasi dan menjalankan sistem SEEKEM pada lingkungan pengembangan lokal Anda.

### 2.1. Prasyarat Sistem
Sebelum memulai proses instalasi, pastikan sistem operasi Anda telah dipasangi perangkat lunak berikut:
- **Node.js**: Versi 16 atau yang lebih baru.
- **Python**: Versi 3.9 atau yang lebih baru.
- **PostgreSQL**: Telah terpasang dan beroperasi secara aktif.

### 2.2. Konfigurasi Sistem Inti (*Backend* / FastAPI)
Sistem inti dikembangkan memanfaatkan kerangka kerja Python (FastAPI). Lakukan langkah-langkah di bawah ini untuk inisialisasi:

1. **Navigasi Direktori**  
   Buka aplikasi terminal dan arahkan ke direktori server sistem inti.
   ```bash
   cd 03_Source_Code/backend
   ```

2. **Inisialisasi Lingkungan Virtual (*Virtual Environment*)**  
   Buat dan aktifkan lingkungan virtual untuk mengisolasi dependensi proyek.
   - Lingkungan Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - Lingkungan Mac/Linux:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. **Pemasangan Dependensi**  
   Pasang seluruh modul Python yang dibutuhkan menggunakan alat bantu manajer paket.
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi Variabel Lingkungan**  
   Buatlah sebuah berkas bernama `.env` di dalam direktori tersebut dan definisikan kredensial sistem Anda sebagaimana contoh berikut.
   ```env
   DATABASE_URL=postgresql://<nama_user>:<kata_sandi>@localhost:5432/<nama_database>
   SECRET_KEY=<kunci_rahasia_sistem>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   
   CLOUDINARY_CLOUD_NAME=<nama_cloud_anda>
   CLOUDINARY_API_KEY=<kunci_api_anda>
   CLOUDINARY_API_SECRET=<rahasia_api_anda>
   
   GAS_EMAIL_URL=<url_webhook_google_apps_script>
   FRONTEND_URL=http://localhost:5173
   ```

5. **Migrasi Basis Data**  
   Jalankan eksekusi Alembic guna membangun skema struktur tabel pada basis data yang terhubung.
   ```bash
   alembic upgrade head
   ```

6. **Menjalankan Server**  
   Nyalakan server sistem inti secara lokal menggunakan Uvicorn.
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   > **Catatan**: Setelah server berhasil dijalankan, Anda dapat mengakses layanan API pada alamat `http://localhost:8000`. Kami juga menyediakan Dokumentasi Interaktif (*Swagger UI*) yang bisa dilihat secara langsung melalui tautan `http://localhost:8000/docs`.

### 2.3. Konfigurasi Antarmuka Pengguna (*Frontend* / React)
Antarmuka pengguna dikembangkan berbasis ekosistem React.js dan Vite. Langkah pengaturannya adalah sebagai berikut:

1. **Navigasi Direktori**  
   Buka jendela terminal baru (sementara biarkan server inti tetap berjalan) dan arahkan menuju direktori antarmuka pengguna.
   ```bash
   cd 03_Source_Code/src
   ```

2. **Pemasangan Dependensi**  
   Unduh seluruh pustaka dan kerangka kerja yang dibutuhkan menggunakan *Node Package Manager*.
   ```bash
   npm install
   ```

3. **Konfigurasi Variabel Lingkungan**  
   Buat sebuah berkas bernama `.env` di dalam direktori tersebut guna mengarahkan titik akhir klien agar terhubung ke server sistem inti.
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

4. **Menjalankan Klien**  
   Nyalakan server pengembangan lokal untuk memuat antarmuka web.
   ```bash
   npm run dev
   ```
   > **Catatan**: Antarmuka aplikasi web akan berjalan dan termuat secara otomatis pada alamat `http://localhost:5173`.

---

## 3. Struktur Repository Proyek
Repositori ini disusun mengikuti pedoman dan instruksi pengelolaan *version control* Git untuk proyek PBL mata kuliah KOM1315 (Keamanan Informasi).

```text
01_Proposal_&_Analisis/
  Proposal_Teknis.pdf
  Threat_Modeling.pdf
02_Design_Documents/
  ERD_Modified.png
  Architecture_Diagram.pdf
  Testing_Plan.pdf
03_Source_Code/
  backend/
  database/
  digital_signature/
  src/
    auth/
04_Reports_&_Paper/
  Monitoring_P7/
  Final_Technical_Report/
  Scientific_Paper/
05_Testing_Logs/
```

### 3.1. Catatan Keamanan Bersama
- Demi keamanan kita bersama, mohon untuk tidak pernah mengunggah (*commit*) data sensitif seperti kunci kriptografi, kata sandi, token akses, atau berkas rahasia apa pun ke dalam repositori publik ini.
- Kami menyarankan agar Anda menyimpan seluruh konfigurasi dan kredensial lokal dengan aman pada berkas lingkungan (*environment files*). Pastikan juga bahwa berkas tersebut telah dilindungi dari proses unggah otomatis melalui pengaturan pada `.gitignore`.
- Untuk menjaga kerapian kolaborasi, mohon pastikan bahwa berkas dokumen, laporan, maupun pembaruan kode sumber selalu diunggah ke dalam direktori yang tepat sesuai dengan tahapan (*milestone*) proyek.
