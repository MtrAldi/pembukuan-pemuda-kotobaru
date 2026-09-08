import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(page_title="Pembukuan Pemuda Kotobaru", page_icon="💰", layout="wide")

# Setup Database SQLite
def init_db():
    conn = sqlite3.connect('kas_kotobaru.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS kas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, jenis TEXT, kategori TEXT, jumlah REAL, keterangan TEXT)''')
    conn.commit()
    return conn

conn = init_db()

st.title("💰 Aplikasi Pembukuan Organisasi Pemuda Kotobaru")
st.markdown("Kelola kas masuk, keluar, dan laporan keuangan organisasi dengan mudah.")

# Sidebar Menu
menu = ["Dashboard", "Input Transaksi", "Data Lengkap & Filter"]
choice = st.sidebar.selectbox("Pilih Menu", menu)

if choice == "Input Transaksi":
    st.header("📝 Catat Transaksi Baru")
    with st.form("transaksi_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.date_input("Tanggal Transaksi", value=datetime.today())
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
        with col2:
            kategori = st.selectbox("Kategori", ["Iuran Anggota", "Sumbangan / Donasi", "Dana Kegiatan", "Konsumsi", "Perlengkapan", "Lain-lain"])
            jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, step=1000.0)
        
        keterangan = st.text_area("Keterangan / Catatan", placeholder="Contoh: Iuran bulanan pemuda RT 01 / Beli bola voli")
        
        submitted = st.form_submit_button("Simpan Transaksi")
        if submitted:
            c = conn.cursor()
            c.execute("INSERT INTO kas (tanggal, jenis, kategori, jumlah, keterangan) VALUES (?,?,?,?,?)",
                      (str(tanggal), jenis, kategori, jumlah, keterangan))
            conn.commit()
            st.success("✅ Transaksi berhasil disimpan!")

elif choice == "Dashboard":
    st.header("📊 Ringkasan Keuangan")
    
    df = pd.read_sql_query("SELECT * FROM kas", conn)
    
    if not df.empty:
        pemasukan = df[df['jenis'] == 'Pemasukan']['jumlah'].sum()
        pengeluaran = df[df['jenis'] == 'Pengeluaran']['jumlah'].sum()
        saldo = pemasukan - pengeluaran
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Saldo Total Kas", f"Rp {saldo:,.0f}")
        col2.metric("📈 Total Pemasukan", f"Rp {pemasukan:,.0f}")
        col3.metric("📉 Total Pengeluaran", f"Rp {pengeluaran:,.0f}")
        
        st.markdown("---")
        st.subheader("Grafik / Riwayat Singkat")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Belum ada data transaksi. Silakan input melalui menu **Input Transaksi**.")

elif choice == "Data Lengkap & Filter":
    st.header("📋 Data Riwayat Transaksi")
    df = pd.read_sql_query("SELECT * FROM kas", conn)
    
    if not df.empty:
        # Filter berdasarkan jenis
        filter_jenis = st.multiselect("Filter Jenis", ["Pemasukan", "Pengeluaran"], default=["Pemasukan", "Pengeluaran"])
        filtered_df = df[df['jenis'].isin(filter_jenis)]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Tombol Download CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan (CSV)",
            data=csv,
            file_name=f"laporan_kas_kotobaru_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada data untuk ditampilkan.")
