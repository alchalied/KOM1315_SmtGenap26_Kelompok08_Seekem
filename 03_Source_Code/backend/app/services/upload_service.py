import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
import uuid
import anyio
from app.cores.config import settings

# Konfigurasi Cloudinary dari environment
cloudinary_url = getattr(settings, "CLOUDINARY_URL", None)
if cloudinary_url:
    cloudinary.config(cloudinary_url=cloudinary_url)
else:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )

class UploadService:
    @staticmethod
    async def upload_image(file: UploadFile) -> str:
        if not settings.cloudinary_configured:
            raise HTTPException(status_code=500, detail="Konfigurasi Cloudinary belum diatur di .env")

        try:
            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(status_code=400, detail="File kosong")

            public_id = str(uuid.uuid4())
            folder = settings.CLOUDINARY_UPLOAD_FOLDER

            def _upload():
                return cloudinary.uploader.upload(
                    file_bytes,
                    public_id=public_id,
                    folder=folder,
                    resource_type="image",
                    overwrite=True,
                )

            result = await anyio.to_thread.run_sync(_upload)
            secure_url = result.get("secure_url") or result.get("url")
            if not secure_url:
                raise HTTPException(status_code=502, detail="Gagal mendapatkan URL hasil upload Cloudinary")

            return secure_url
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Gagal mengunggah ke Cloudinary: {str(exc)}")

    @staticmethod
    async def upload_base64_image(base64_data: str) -> str:
        """Mengunggah gambar dari string base64 ke Cloudinary dan mengembalikan URL."""
        if not settings.cloudinary_configured:
            raise HTTPException(status_code=500, detail="Konfigurasi Cloudinary belum diatur di .env")

        if not base64_data or not base64_data.startswith("data:image"):
            # Jika bukan base64 image (mungkin URL biasa atau kosong)
            return base64_data

        try:
            public_id = str(uuid.uuid4())
            folder = settings.CLOUDINARY_UPLOAD_FOLDER

            def _upload():
                return cloudinary.uploader.upload(
                    base64_data,
                    public_id=public_id,
                    folder=folder,
                    resource_type="image",
                    overwrite=True,
                )

            result = await anyio.to_thread.run_sync(_upload)
            secure_url = result.get("secure_url") or result.get("url")
            if not secure_url:
                raise HTTPException(status_code=502, detail="Gagal mendapatkan URL hasil upload Cloudinary")

            return secure_url
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Gagal mengunggah base64 ke Cloudinary: {str(exc)}")
