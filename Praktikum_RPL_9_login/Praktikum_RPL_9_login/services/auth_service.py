import re

from repositories.pengguna_repository import PenggunaRepository
from services.password_hasher import PasswordHasher


class AuthError(Exception):
    """Error yang pesannya aman ditampilkan ke pengguna."""


class AuthService:
    """Cuma ngurus aturan bisnis daftar dan login."""

    PANJANG_PASSWORD_MINIMAL = 8
    POLA_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, repo: PenggunaRepository, hasher: PasswordHasher):
        self.repo = repo
        self.hasher = hasher

    def daftar(self, nama: str, email: str, password: str, ulangi_password: str):
        nama = nama.strip()
        email = self._rapikan_email(email)

        if nama == "":
            raise AuthError("Nama tidak boleh kosong.")
        if not self.POLA_EMAIL.match(email):
            raise AuthError("Format email tidak valid.")
        if len(password) < self.PANJANG_PASSWORD_MINIMAL:
            raise AuthError(
                f"Password minimal {self.PANJANG_PASSWORD_MINIMAL} karakter."
            )
        if password != ulangi_password:
            raise AuthError("Konfirmasi password tidak sama.")
        if self.repo.cari_berdasarkan_email(email) is not None:
            raise AuthError("Email sudah terdaftar, silakan masuk.")

        hash_password = self.hasher.hash_password(password)
        return self.repo.simpan_pengguna(nama, email, hash_password, "email")

    def masuk(self, email: str, password: str):
        pengguna = self.repo.cari_berdasarkan_email(self._rapikan_email(email))
        # Pesan sengaja disamakan supaya tidak membocorkan email mana yang terdaftar
        pesan_gagal = "Email atau password salah."

        if pengguna is None or pengguna.password_hash is None:
            raise AuthError(pesan_gagal)
        if not self.hasher.verifikasi(password, pengguna.password_hash):
            raise AuthError(pesan_gagal)
        return pengguna

    def masuk_dengan_google(self, email: str, nama: str):
        email = self._rapikan_email(email)
        pengguna = self.repo.cari_berdasarkan_email(email)
        if pengguna is None:
            nama_akhir = nama.strip() or email.split("@")[0]
            pengguna = self.repo.simpan_pengguna(nama_akhir, email, None, "google")
        return pengguna

    def _rapikan_email(self, email: str) -> str:
        return email.strip().lower()
