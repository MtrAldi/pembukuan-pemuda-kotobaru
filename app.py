import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(page_title="Pembukuan Pemuda Kotobaru", page_icon="💰", layout="wide")

# --- Konfigurasi Admin ---
# Password default. Untuk produksi di Streamlit Cloud, ganti lewat:
# Settings -> Secrets -> ADMIN_PASSWORD = "password-rahasia-anda"
def get_admin_password():
    try:
        return st.secrets.get("ADMIN_PASSWORD", "admin123")
    except Exception:
        return "admin123"

ADMIN_PASSWORD = get_admin_password()

# --- Setup Database SQLite ---
def init_db():
    conn = sqlite3.connect('kas_kotobaru.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, jenis TEXT, kategori TEXT, jumlah REAL, keterangan TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def load_data():
    return pd.read_sql_query("SELECT * FROM kas ORDER BY id DESC", conn)

def rupiah(x):
    return f"Rp {x:,.0f}"

# --- Session state login ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

st.title("💰 Aplikasi Pembukuan Organisasi Pemuda Kotobaru")
st.markdown("Kelola kas masuk, keluar, dan laporan keuangan organisasi dengan mudah.")

# --- Sidebar: Login / Status ---
st.sidebar.header("🔐 Akses")
if st.session_state.is_admin:
    st.sidebar.success("Login sebagai **Admin** 👑")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()
else:
    st.sidebar.info("Mode **Anggota** 👀 (lihat saja)")
    with st.sidebar.expander("Login sebagai Admin"):
        pwd = st.text_input("Password Admin", type="password", key="admin_pwd")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.success("Login berhasil! Selamat datang, Admin.")
                st.rerun()
            else:
                st.error("Password salah.")

is_admin = st.session_state.is_admin

# --- Menu berbeda per peran ---
if is_admin:
    menu = ["Dashboard", "Input Transaksi", "Kelola Data (Edit/Hapus)", "Data Lengkap & Filter"]
else:
    menu = ["Dashboard", "Rincian Keuangan"]

choice = st.sidebar.selectbox("Pilih Menu", menu)

# ================= DASHBOARD (semua bisa lihat) =================
if choice == "Dashboard":
    st.header("📊 Ringkasan Keuangan")
    df = load_data()
    if not df.empty:
        pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
        pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
        saldo = pemasukan - pengeluaran

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Saldo Total Kas", rupiah(saldo))
        col2.metric("📈 Total Pemasukan", rupiah(pemasukan))
        col3.metric("📉 Total Pengeluaran", rupiah(pengeluaran))

        st.markdown("---")
        st.subheader("Riwayat Singkat (Terbaru)")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("Belum ada data transaksi." + (" Silakan input melalui menu **Input Transaksi**." if is_admin else ""))

# ================= RINCIAN (anggota: read-only lengkap) =================
elif choice == "Rincian Keuangan":
    st.header("📋 Rincian Keuangan — Uang Masuk & Keluar")
    st.caption("Mode Anggota: hanya melihat, tidak bisa menambah/mengubah/menghapus data.")
    df = load_data()
    if not df.empty:
        tab_masuk, tab_keluar, tab_semua = st.tabs(["💵 Uang Masuk", "💸 Uang Keluar", "📑 Semua"])
        with tab_masuk:
            df_in = df[df['jenis'] == 'Pemasukan']
            st.metric("Total Uang Masuk", rupiah(df_in['jumlah'].sum()))
            st.dataframe(df_in[['tanggal', 'kategori', 'jumlah', 'keterangan']], use_container_width=True)
        with tab_keluar:
            df_out = df[df['jenis'] == 'Pengeluaran']
            st.metric("Total Uang Keluar", rupiah(df_out['jumlah'].sum()))
            st.dataframe(df_out[['tanggal', 'kategori', 'jumlah', 'keterangan']], use_container_width=True)
        with tab_semua:
            filter_jenis = st.multiselect("Filter Jenis", ["Pemasukan", "Pengeluaran"],
                                          default=["Pemasukan", "Pengeluaran"], key="anggota_filter")
            st.dataframe(df[df['jenis'].isin(filter_jenis)], use_container_width=True)
    else:
        st.info("Belum ada data untuk ditampilkan.")

# ================= ADMIN SAJA =================
elif choice == "Input Transaksi":
    if not is_admin:
        st.warning("⛔ Hanya admin yang bisa menambah transaksi. Silakan login sebagai admin.")
        st.stop()
    st.header("📝 Catat Transaksi Baru")
    with st.form("transaksi_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.date_input("Tanggal Transaksi", value=datetime.today())
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
        with col2:
            kategori = st.selectbox("Kategori", ["Iuran Anggota", "Sumbangan / Donasi", "Dana Kegiatan",
                                                 "Konsumsi", "Perlengkapan", "Lain-lain"])
            jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, step=1000.0)
        keterangan = st.text_area("Keterangan / Uraian", placeholder="Contoh: Iuran bulanan RT 01 / Beli bola voli")
        if st.form_submit_button("Simpan Transaksi"):
            if jumlah <= 0:
                st.error("Jumlah harus lebih dari 0.")
            else:
                c = conn.cursor()
                c.execute("INSERT INTO kas (tanggal, jenis, kategori, jumlah, keterangan) VALUES (?,?,?,?,?)",
                          (str(tanggal), jenis, kategori, jumlah, keterangan))
                conn.commit()
                st.success("✅ Transaksi berhasil disimpan!")

elif choice == "Kelola Data (Edit/Hapus)":
    if not is_admin:
        st.warning("⛔ Hanya admin yang bisa mengelola data.")
        st.stop()
    st.header("🛠️ Kelola Data (Edit / Hapus)")
    df = load_data()
    if df.empty:
        st.info("Belum ada data.")
    else:
        st.dataframe(df, use_container_width=True)
        ids = df['id'].tolist()
        sel_id = st.selectbox("Pilih ID transaksi", ids)
        row = df[df['id'] == sel_id].iloc[0]

        with st.form("edit_form"):
            e_tanggal = st.text_input("Tanggal (YYYY-MM-DD)", value=str(row['tanggal']))
            e_jenis = st.selectbox("Jenis", ["Pemasukan", "Pengeluaran"],
                                   index=0 if row['jenis'] == 'Pemasukan' else 1)
            e_kategori = st.text_input("Kategori", value=str(row['kategori']))
            e_jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, value=float(row['jumlah']), step=1000.0)
            e_ket = st.text_area("Keterangan / Uraian", value=str(row['keterangan'] or ""))
            col_a, col_b = st.columns(2)
            with col_a:
                do_update = st.form_submit_button("💾 Simpan Perubahan")
            with col_b:
                do_delete = st.form_submit_button("🗑️ Hapus Transaksi Ini", type="primary")
            if do_update:
                c = conn.cursor()
                c.execute("UPDATE kas SET tanggal=?, jenis=?, kategori=?, jumlah=?, keterangan=? WHERE id=?",
                          (e_tanggal, e_jenis, e_kategori, e_jumlah, e_ket, int(sel_id)))
                conn.commit()
                st.success(f"✅ Transaksi ID {sel_id} diperbarui.")
                st.rerun()
            if do_delete:
                c = conn.cursor()
                c.execute("DELETE FROM kas WHERE id=?", (int(sel_id),))
                conn.commit()
                st.success(f"🗑️ Transaksi ID {sel_id} dihapus.")
                st.rerun()

elif choice == "Data Lengkap & Filter":
    if not is_admin:
        st.warning("⛔ Hanya admin yang bisa mengakses menu ini.")
        st.stop()
    st.header("📋 Data Riwayat Transaksi (Admin)")
    df = load_data()
    if not df.empty:
        filter_jenis = st.multiselect("Filter Jenis", ["Pemasukan", "Pengeluaran"],
                                      default=["Pemasukan", "Pengeluaran"], key="admin_filter")
        filtered_df = df[df['jenis'].isin(filter_jenis)]
        st.dataframe(filtered_df, use_container_width=True)
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan (CSV)",
            data=csv,
            file_name=f"laporan_kas_kotobaru_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada data untuk ditampilkan.")
