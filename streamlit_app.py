import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time

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

# Di dalam loop data saham:
df['RSI'] = df.ta.rsi(length=14)
df['SMA20'] = df.ta.sma(length=20)
df['SMA200'] = df.ta.sma(length=200)

# Contoh perbaikan dalam loop
for kode_asal in daftar_saham:
    ticker = f"{kode_asal}.JK"  # Menambahkan .JK secara otomatis
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    
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

# Simpan hasil scan dalam list
hasil_scan = []

# ... proses download data ...

# Cek apakah data cukup untuk SMA200
if len(df) > 200:
    last_row = df.iloc[-1]
    vol_ratio = last_row['Volume'] / df['Volume'].rolling(20).mean().iloc[-1]
    
    # Syarat Filter (Sesuaikan dengan slider)
    if (last_row['RSI'] >= rsi_val and 
        vol_ratio >= vol_val and 
        last_row['Close'] > last_row['SMA20'] and 
        last_row['Close'] > last_row['SMA200']):
        
        hasil_scan.append({
            "Kode": kode_asal,
            "Harga": last_row['Close'],
            "RSI": round(last_row['RSI'], 2),
            "Vol Ratio": round(vol_ratio, 2),
            # Tambahkan kolom lainnya...
        })

# Tampilkan Tabel
if hasil_scan:
    st.success(f"{len(hasil_scan)} saham lolos!")
    df_final = pd.DataFrame(hasil_scan)
    st.dataframe(df_final) # Ini akan memunculkan tabel seperti di gambar
    
    # Tombol Download CSV
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="hasil_scan.csv")
else:
    st.warning("Tidak ada yang lolos.")

# --- Judul & UI (Sesuai Gambar Sebelumnya) ---
st.title("🔥 IDX Swing Screener Real-Time")

# ... (bagian slider rsi, vol, dll diletakkan di sini) ...

# Tombol Scan
if st.button("🚀 Scan Sekarang"):
    # 1. Inisialisasi Progress Bar (Loading Scene)
    # Ini yang menciptakan garis biru berjalan seperti di gambar 28
    progress_text = "Sedang memindai pasar saham IDX. Harap tunggu..."
    my_bar = st.progress(0, text=progress_text)
    
    # Contoh daftar saham (ganti dengan pembacaan Excel kamu)
    stock_list = ["ASGR.JK", "LPCK.JK", "GOLF.JK", "UANG.JK", "MLPL.JK", "ELSA.JK"]
    total_stocks = len(stock_list)
    results = []

    # 2. Proses Scanning dengan Update Progress
    for i, ticker in enumerate(stock_list):
        # Update progress bar (0.0 sampai 1.0)
        progress_val = (i + 1) / total_stocks
        my_bar.progress(progress_val, text=f"Memproses {ticker} ({i+1}/{total_stocks})")
        
        try:
            # Ambil data dari yfinance
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            
            if not df.empty and len(df) > 200:
                # Contoh Logika Sederhana (sesuaikan dengan filter slider)
                last_price = df['Close'].iloc[-1]
                # (Tambahkan hitungan RSI & SMA di sini)
                
                # Masukkan ke list jika lolos filter
                results.append({
                    "Kode": ticker.replace(".JK", ""),
                    "Harga": round(last_price, 0),
                    "RSI": 75.5, # Contoh nilai statis
                    "Vol Ratio": 5.2, # Contoh nilai statis
                    "% 1B": "20.5%",
                    "Cap (T)": 4.5
                })
        except Exception as e:
            continue

    # 3. Hilangkan Progress Bar setelah selesai
    time.sleep(0.5)
    my_bar.empty()

    # 4. Tampilkan Hasil (Seperti Screenshot 27)
    if results:
        st.success(f"{len(results)} saham lolos!")
        df_final = pd.DataFrame(results)
        
        # Menampilkan Tabel
        st.dataframe(df_final, use_container_width=True)
        
        # Tombol Download
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="hasil_scan.csv")
    else:
        # Tampilan jika tidak ada yang lolos 
        st.warning("Tidak ada yang lolos.")
