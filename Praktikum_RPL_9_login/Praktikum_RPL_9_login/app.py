import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.model import Base
from repositories.pengguna_repository import PenggunaRepository
from repositories.repository import MahasiswaRepository
from services.auth_service import AuthError, AuthService
from services.password_hasher import PasswordHasher
from services.service import PrediksiService

STATUS_LULUS = "Lulus Tepat Waktu"
PENYEDIA_GOOGLE = "google"

st.set_page_config(page_title="Prediksi Kelulusan", page_icon="🎓")


@st.cache_resource
def inisialisasi_database():
    load_dotenv()
    # check_same_thread=False karena Streamlit menjalankan script di thread berbeda
    engine = create_engine(
        os.getenv("DATABASE_URL"), connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------- Helper sesi login ----------

def simpan_sesi(pengguna):
    st.session_state["pengguna_nama"] = pengguna.nama
    st.session_state["pengguna_email"] = pengguna.email
    st.session_state["metode_login"] = pengguna.metode_login


def sudah_login() -> bool:
    return "pengguna_email" in st.session_state


def google_tersedia() -> bool:
    """Login Google aktif kalau secrets [auth.google] sudah diisi."""
    try:
        return PENYEDIA_GOOGLE in st.secrets["auth"]
    except Exception:
        return False


def sinkronkan_login_google(auth_service: AuthService):
    """Kalau pengguna baru selesai login Google, catat ke sesi aplikasi."""
    if sudah_login() or not google_tersedia():
        return
    if getattr(st.user, "is_logged_in", False):
        pengguna = auth_service.masuk_dengan_google(st.user.email, st.user.name or "")
        simpan_sesi(pengguna)


def keluar():
    metode = st.session_state.get("metode_login")
    for kunci in ("pengguna_nama", "pengguna_email", "metode_login"):
        st.session_state.pop(kunci, None)
    if metode == "google":
        st.logout()


# ---------- Halaman login ----------

def tampilkan_form_masuk(auth_service: AuthService):
    with st.form("form_masuk"):
        email = st.text_input("Email", placeholder="nama@email.com")
        password = st.text_input("Password", type="password")
        kirim = st.form_submit_button("Masuk")

    if kirim:
        try:
            simpan_sesi(auth_service.masuk(email, password))
            st.rerun()
        except AuthError as error:
            st.error(str(error))


def tampilkan_form_daftar(auth_service: AuthService):
    with st.form("form_daftar"):
        nama = st.text_input("Nama lengkap")
        email = st.text_input("Email", placeholder="nama@email.com", key="daftar_email")
        password = st.text_input("Password (min. 8 karakter)", type="password", key="daftar_password")
        ulangi_password = st.text_input("Ulangi password", type="password")
        kirim = st.form_submit_button("Daftar")

    if kirim:
        try:
            simpan_sesi(auth_service.daftar(nama, email, password, ulangi_password))
            st.rerun()
        except AuthError as error:
            st.error(str(error))


def tampilkan_tombol_google():
    st.markdown("<div style='text-align:center'>atau</div>", unsafe_allow_html=True)
    if google_tersedia():
        st.button(
            "Lanjutkan dengan Google",
            icon=":material/login:",
            on_click=st.login,
            args=(PENYEDIA_GOOGLE,),
        )
    else:
        st.button("Lanjutkan dengan Google", disabled=True)
        st.caption(
            "Login Google belum diaktifkan. Lihat `.streamlit/secrets.toml.example` "
            "untuk cara mengisinya."
        )


def halaman_login(auth_service: AuthService):
    st.title("🎓 Sistem Prediksi Kelulusan")
    st.caption("Silakan masuk atau daftar untuk melanjutkan.")

    tab_masuk, tab_daftar = st.tabs(["Masuk", "Daftar"])
    with tab_masuk:
        tampilkan_form_masuk(auth_service)
    with tab_daftar:
        tampilkan_form_daftar(auth_service)

    tampilkan_tombol_google()


# ---------- Halaman utama (prediksi) ----------

def tampilkan_hasil(nama: str, status: str):
    if status == STATUS_LULUS:
        st.success(f"🎉 **{nama}** dinyatakan **{status}**!")
    else:
        st.error(f"❌ **{nama}** dinyatakan **{status}**.")


def tampilkan_riwayat(repo: MahasiswaRepository):
    st.divider()
    st.subheader("📋 Riwayat Prediksi")
    data_db = repo.ambil_semua_data()
    if data_db:
        list_data = [
            {"Nama": d.nama, "IPK": d.ipk, "SKS": d.sks, "Status": d.status_kelulusan}
            for d in data_db
        ]
        st.dataframe(pd.DataFrame(list_data), width="stretch")
    else:
        st.info("Belum ada data yang tersimpan.")


def tampilkan_sidebar_pengguna():
    with st.sidebar:
        st.write(f"Halo, **{st.session_state['pengguna_nama']}** 👋")
        st.caption(st.session_state["pengguna_email"])
        st.button("Keluar", on_click=keluar)


def halaman_utama(repo: MahasiswaRepository, service: PrediksiService):
    tampilkan_sidebar_pengguna()
    st.title("🎓 Sistem Prediksi Kelulusan")

    with st.form("form_input"):
        nama = st.text_input("Nama Mahasiswa")
        ipk = st.number_input("IPK (0.0 - 4.0)", min_value=0.0, max_value=4.0, step=0.01)
        sks = st.number_input("Total SKS", min_value=0, step=1)
        tombol_proses = st.form_submit_button("Prediksi & Simpan")

    if tombol_proses:
        if nama.strip() == "":
            st.warning("⚠️ Nama tidak boleh kosong!")
        else:
            hasil_status = service.tentukan_kelulusan(ipk, sks)
            repo.simpan_data(nama.strip(), ipk, int(sks), hasil_status)
            tampilkan_hasil(nama.strip(), hasil_status)
            st.toast("Data berhasil disimpan!")

    tampilkan_riwayat(repo)


# ---------- Merangkai semua layer (Dependency Injection) ----------

db_session = inisialisasi_database()
repo = MahasiswaRepository(db_session)
service = PrediksiService()
auth_service = AuthService(PenggunaRepository(db_session), PasswordHasher())

sinkronkan_login_google(auth_service)

if sudah_login():
    halaman_utama(repo, service)
else:
    halaman_login(auth_service)
