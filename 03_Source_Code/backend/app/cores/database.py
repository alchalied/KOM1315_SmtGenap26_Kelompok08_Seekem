from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.cores.config import settings

# Engine database (gunakan pool_pre_ping untuk mengecek koneksi terputus)
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# SessionLocal untuk interaksi dengan database di setiap request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
