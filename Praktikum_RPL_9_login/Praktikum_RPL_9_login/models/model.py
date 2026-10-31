from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Mahasiswa(Base):
    """Struktur tabel mahasiswa (data prediksi kelulusan)."""

    __tablename__ = "mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String)
    ipk = Column(Float)
    sks = Column(Integer)
    status_kelulusan = Column(String)


class Pengguna(Base):
    """Struktur tabel pengguna untuk login (email atau Google)."""

    __tablename__ = "pengguna"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String)  # kosong kalau daftar lewat Google
    metode_login = Column(String, nullable=False)  # "email" atau "google"
