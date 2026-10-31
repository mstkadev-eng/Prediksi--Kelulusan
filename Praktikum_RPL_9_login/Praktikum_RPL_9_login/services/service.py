class PrediksiService:
    """Cuma ngurus aturan bisnis kelulusan."""

    BATAS_IPK_MINIMAL = 3.0
    BATAS_SKS_MINIMAL = 140

    def tentukan_kelulusan(self, ipk: float, sks: int) -> str:
        if ipk >= self.BATAS_IPK_MINIMAL and sks >= self.BATAS_SKS_MINIMAL:
            return "Lulus Tepat Waktu"
        return "Tidak Lulus"
