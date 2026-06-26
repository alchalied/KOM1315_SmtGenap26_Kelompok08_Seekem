from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.cores.database import engine
from app.models.base import Base
# Import all models here to ensure they are registered with Base before create_all
from app.models import user, laporan, klaim, notifikasi, audit_log, activity_log
from app.api import (
    auth,
    items as items_api,
    admin as admin_api,
    laporan as laporan_api,
    klaim as klaim_api,
    notifikasi as notifikasi_api,
    admin_dashboard as admin_dashboard_api,
    history as history_api,
    contact as contact_api,
)

app = FastAPI(
    title="LostnFound-IPB API",
    description="API untuk sistem pelaporan kehilangan dan penemuan barang di IPB",
    version="2.0.0"
)

import os

# CORS — Izinkan FE Vite dev server mengakses BE
cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cors_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router yang digunakan langsung oleh Frontend (Source of Truth) ──
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(items_api.router, prefix="/api/items", tags=["items"])
app.include_router(admin_api.router, prefix="/api/admin", tags=["admin"])
app.include_router(history_api.router, prefix="/api/history", tags=["history"])
app.include_router(contact_api.router, prefix="/api/laporan", tags=["contact_reporter"])

# ── Router internal / legacy (tetap tersedia untuk Swagger testing) ──
app.include_router(laporan_api.router, prefix="/api/laporan", tags=["laporan (internal)"])
app.include_router(klaim_api.router, prefix="/api/klaim", tags=["klaim (internal)"])
app.include_router(notifikasi_api.router, prefix="/api/notifikasi", tags=["notifikasi"])
app.include_router(admin_dashboard_api.router, prefix="/api/admin/dashboard", tags=["admin_dashboard (internal)"])

# Route dasar untuk testing
@app.get("/")
async def root():
    return {"message": "Selamat datang di LostnFound-IPB API v2"}

# Jika Anda ingin menjalankan server langsung dari file ini
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
