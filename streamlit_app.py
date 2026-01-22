import streamlit as st
import pandas as pd
import yfinance as yf

# Mengambil data saham BCA
ticker = "BBCA.JK"
data = yf.download(ticker, period="1y", interval="1d")

# Menampilkan 5 data terakhir
print(data.tail())
# Konfigurasi Halaman
st.set_page_config(page_title="IDX Swing Screener", layout="wide")

# Judul dan Deskripsi
st.title("🔥 IDX Swing Screener Real-Time by jamilstempel.com")
st.markdown("""
Screener swing trading fokus momentum, uptrend, & volume.  
Data **real-time/delayed** dari API RTA. Scan malam hari untuk closing akurat.
""")

# File Uploader
st.markdown("---")
uploaded_file = st.file_uploader(
    "Upload Daftar Saham Excel dari IDX (kolom A 'No' kolom B 'Kode' kolom selanjutnya hapus)", 
    type=["xlsx"]
)

st.info("IDX List (Scan Now). Upload Excel untuk full scan.")

# Bagian Slider Input
st.markdown("### Super Agresif 🔥 : RSI: 50.00, Min Volume: 3.0, % Change 1 bulan: 15, Market Cap: 1.5 dan 5 T.")

# Membuat 2 Kolom untuk Slider
col1, col2 = st.columns(2)

with col1:
    rsi_val = st.slider("Min RSI (14)", 0.0, 100.0, 50.0)
    vol_val = st.slider("Min Volume Today vs Avg 20 hari (x)", 0.0, 10.0, 3.0)

with col2:
    pct_change = st.slider("Min % Change 1 Bulan", 0.0, 100.0, 15.0)
    market_cap = st.slider("Min Market Cap (Triliun Rp)", 0.0, 100.0, 1.5)

st.markdown("**✓ Filter wajib: Harga > SMA 20 & SMA 200**")

# Tombol Scan
if st.button("🚀 Scan Sekarang"):
    if uploaded_file is not None:
        st.write("Sedang memproses data...")
        # Di sini tempat kamu memasukkan logika screening datamu
    else:
        st.warning("Silakan upload file Excel terlebih dahulu atau gunakan data default.")

# Footer/Status
st.markdown("---")
st.caption("Malam 20 Jan 2026 – data closing akurat sekarang. Refresh untuk update.")
