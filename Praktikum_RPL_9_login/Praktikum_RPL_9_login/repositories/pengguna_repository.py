from sqlalchemy.orm import Session

from models.model import Pengguna


class PenggunaRepository:
    """Cuma ngurus simpan dan cari data pengguna di database."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def cari_berdasarkan_email(self, email: str):
        return self.db.query(Pengguna).filter(Pengguna.email == email).first()

    def simpan_pengguna(
        self, nama: str, email: str, password_hash: str | None, metode_login: str
    ) -> Pengguna:
        pengguna_baru = Pengguna(
            nama=nama,
            email=email,
            password_hash=password_hash,
            metode_login=metode_login,
        )
        self.db.add(pengguna_baru)
        self.db.commit()
        self.db.refresh(pengguna_baru)
        return pengguna_baru
