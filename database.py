import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# FIX: Import dari package yang benar
from Transkrip.models import Base

# Ambil DATABASE_URL dari environment variable agar fleksibel di Docker
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root@transkrip-db:3306/transkrip_db"
    #"postgresql://postgres:password@transkrip-db:5432/transkrip_db"
)

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

MAX_RETRIES = 10
for i in range(MAX_RETRIES):
    try:
        # create_all hanya membuat tabel yang belum ada (idempotent).
        # Aman dijalankan berulang kali.
        Base.metadata.create_all(bind=engine)
        print("✅ Tabel database berhasil dibuat!")
        break
    except Exception as e:
        print(f"⏳ Database belum siap ({i+1}/{MAX_RETRIES}): {e}")
        if i < MAX_RETRIES - 1:
            time.sleep(3)
        else:
            print("❌ Gagal konek ke database setelah beberapa percobaan.")
            raise