import os
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
dotenv_path = os.path.join(backend_dir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv() # Fallback ke direktori saat ini

class Settings:
    PROJECT_NAME: str = "LostnFound-IPB API"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lostnfound")
    # Mengambil dari JWT_SECRET_KEY, fallback ke SECRET_KEY bawaan jika kosong
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # Konfigurasi Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_UPLOAD_FOLDER: str = os.getenv("CLOUDINARY_UPLOAD_FOLDER", "lostnfound")

    @property
    def cloudinary_configured(self) -> bool:
        return bool(self.CLOUDINARY_CLOUD_NAME and self.CLOUDINARY_API_KEY and self.CLOUDINARY_API_SECRET)

settings = Settings()
