import hashlib
import hmac
import os


class PasswordHasher:
    """Cuma ngurus hash dan verifikasi password (PBKDF2 + salt acak)."""

    JUMLAH_ITERASI = 200_000
    PANJANG_SALT = 16

    def hash_password(self, password: str) -> str:
        salt = os.urandom(self.PANJANG_SALT)
        hasil = self._turunkan_kunci(password, salt)
        return f"{salt.hex()}${hasil.hex()}"

    def verifikasi(self, password: str, hash_tersimpan: str) -> bool:
        try:
            salt_hex, hasil_hex = hash_tersimpan.split("$")
            salt = bytes.fromhex(salt_hex)
            hasil_tersimpan = bytes.fromhex(hasil_hex)
        except ValueError:
            return False
        hasil_baru = self._turunkan_kunci(password, salt)
        return hmac.compare_digest(hasil_baru, hasil_tersimpan)

    def _turunkan_kunci(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.JUMLAH_ITERASI
        )
