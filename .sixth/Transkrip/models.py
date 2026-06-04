from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class StatusNilai(str, enum.Enum):
    BELUM_TERNILAI = "belum_ternilai"
    SUDAH_TERNILAI = "sudah_ternilai"

class KRS(Base):
    __tablename__ = "krs"
    id_krs     = Column(Integer, primary_key=True, autoincrement=True)
    id_prs     = Column(Integer, nullable=False)          # FK ke PRS service
    status_nilai = Column(
        Enum(StatusNilai), default=StatusNilai.BELUM_TERNILAI
    )

class KHS(Base):
    __tablename__ = "khs"
    id_khs       = Column(Integer, primary_key=True, autoincrement=True)
    id_krs       = Column(Integer, ForeignKey("krs.id_krs"), nullable=False)
    semester     = Column(String(10), nullable=False)
    tahun_ajaran = Column(String(10), nullable=False)

class KHSDetail(Base):
    __tablename__ = "khs_detail"
    id_khs_detail = Column(Integer, primary_key=True, autoincrement=True)
    id_khs        = Column(Integer, ForeignKey("khs.id_khs"), nullable=False)
    id_nilai      = Column(Integer, ForeignKey("nilai.id_nilai"), nullable=False)
    sks           = Column(Integer, nullable=False)
    nilai_huruf   = Column(String(2))
    nilai_akhir   = Column(Float)

class Nilai(Base):
    __tablename__ = "nilai"
    id_nilai    = Column(Integer, primary_key=True, autoincrement=True)
    id_matkul   = Column(Integer, nullable=False)   # FK ke Master service
    id_krs      = Column(Integer, ForeignKey("krs.id_krs"), nullable=False)
    nilai_uts   = Column(Float, nullable=True)
    nilai_uas   = Column(Float, nullable=True)
    nilai_tes1  = Column(Float, nullable=True)
    nilai_tes2  = Column(Float, nullable=True)
    nilai_akhir = Column(Float, nullable=True)
    nilai_huruf = Column(String(2), nullable=True)

class Transkrip(Base):
    __tablename__ = "transkrip"
    id_transkrip  = Column(Integer, primary_key=True, autoincrement=True)
    id_mahasiswa  = Column(Integer, nullable=False)   # FK ke Master service
    total_sks     = Column(Integer, default=0)
    ips           = Column(Float, default=0.0)
    ipk           = Column(Float, default=0.0)

class DetailTranskrip(Base):
    __tablename__ = "detail_transkrip"
    id_detail_transkrip = Column(Integer, primary_key=True, autoincrement=True)
    id_transkrip        = Column(Integer, ForeignKey("transkrip.id_transkrip"))
    id_nilai            = Column(Integer, ForeignKey("nilai.id_nilai"))
    sks                 = Column(Integer)
    nilai_huruf         = Column(String(2))
    nilai_akhir         = Column(Float)