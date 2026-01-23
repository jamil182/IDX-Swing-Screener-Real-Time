import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time

# Konfigurasi Halaman
st.set_page_config(page_title="IDX Swing Screener", layout="wide")

# Judul dan Deskripsi
st.title("🔥 IDX Swing Screener Real-Time by jamilstempel.com")
st.markdown("""
Screener swing trading fokus momentum, uptrend, & volume.  
Data **delayed** dari yfinance (real-time tidak tersedia gratis untuk IDX).  
Scan malam hari untuk closing paling akurat.
""")

st.markdown("---")

# File Uploader
uploaded_file = st.file_uploader(
    "Upload Daftar Saham Excel dari IDX (kolom A 'No', kolom B 'Kode', kolom lain hapus)",
    type=["xlsx"]
)

# Default list jika belum upload
default_stocks = ["ASGR", "LPCK", "GOLF", "UANG", "MLPL", "ELSA", "BBCA", "BBRI", "BMRI", "TLKM"]

if uploaded_file is not None:
    try:
        df_upload = pd.read_excel(uploaded_file, header=None)
        # Ambil kolom B (index 1), skip baris kosong, mulai dari baris data (biasanya baris 2 jika ada header)
        daftar_saham = df_upload.iloc[1:, 1].dropna().astype(str).str.strip().tolist()
        if not daftar_saham:
            st.error("File Excel tidak berisi kode saham yang valid di kolom B.")
            daftar_saham = default_stocks
        else:
            st.success(f"Berhasil load {len(daftar_saham)} saham dari file.")
    except Exception as e:
        st.error(f"Error membaca file: {e}")
        daftar_saham = default_stocks
else:
    daftar_saham = default_stocks
    st.info(f"Menggunakan daftar default ({len(daftar_saham)} saham). Upload Excel untuk full scan IDX.")

# Slider Filter
st.markdown("### 🔧 Pengaturan Filter")
st.markdown("**Super Agresif 🔥 contoh:** RSI ≥ 50, Vol Ratio ≥ 3.0x, % 1 Bulan ≥ 15%, Market Cap ≥ 1.5 T")

col1, col2 = st.columns(2)
with col1:
    rsi_val = st.slider("Min RSI (14)", 0.0, 100.0, 50.0, step=0.5)
    vol_val = st.slider("Min Volume Today vs Avg 20 hari (x)", 0.0, 10.0, 3.0, step=0.1)
with col2:
    pct_change_val = st.slider("Min % Change 1 Bulan", -50.0, 100.0, 15.0, step=0.5)
    market_cap_val = st.slider("Min Market Cap (Triliun Rp)", 0.0, 500.0, 1.5, step=0.1)

st.markdown("**✓ Filter wajib:** Harga > SMA20 > SMA200 (uptrend)")

# Tombol Scan
if st.button("🚀 Scan Sekarang"):
    if not daftar_saham:
        st.warning("Tidak ada daftar saham untuk discan.")
    else:
        st.write("Sedang memproses data...")
        progress_text = "Sedang memindai pasar saham IDX. Harap tunggu..."
        my_bar = st.progress(0, text=progress_text)

        total_stocks = len(daftar_saham)
        results = []

        for i, kode in enumerate(daftar_saham):
            ticker = f"{kode}.JK"
            progress_val = (i + 1) / total_stocks
            my_bar.progress(progress_val, text=f"Memproses {kode} ({i+1}/{total_stocks})")

            try:
                # Download data 1 tahun
                df = yf.download(ticker, period="1y", interval="1d", progress=False)

                if df.empty or len(df) < 200:
                    continue

                # Hitung indikator
                df["RSI"] = ta.rsi(df["Close"], length=14)
                df["SMA20"] = ta.sma(df["Close"], length=20)
                df["SMA200"] = ta.sma(df["Close"], length=200)

                last = df.iloc[-1]

                # Skip jika indikator NaN
                if pd.isna(last["RSI"]) or pd.isna(last["SMA20"]) or pd.isna(last["SMA200"]):
                    continue

                close = last["Close"]
                rsi = last["RSI"]
                sma20 = last["SMA20"]
                sma200 = last["SMA200"]
                vol_today = last["Volume"]
                avg_vol_20 = df["Volume"].rolling(20).mean().iloc[-1]
                vol_ratio = vol_today / avg_vol_20 if avg_vol_20 > 0 else 0

                # % Change 1 bulan (approx 21 hari perdagangan)
                if len(df) >= 22:
                    pct_1m = df["Close"].pct_change(periods=21).iloc[-1] * 100
                else:
                    pct_1m = 0

                # Market Cap (Triliun Rp)
                ticker_obj = yf.Ticker(ticker)
                mc_trillion = ticker_obj.info.get("marketCap", 0) / 1_000_000_000_000

                # Filter
                if (close > sma20 > sma200 and
                    rsi >= rsi_val and
                    vol_ratio >= vol_val and
                    pct_1m >= pct_change_val and
                    mc_trillion >= market_cap_val):

                    results.append({
                        "Kode": kode,
                        "Harga": round(close),
                        "RSI": round(rsi, 2),
                        "Vol Ratio": round(vol_ratio, 2),
                        "% 1B": f"{pct_1m:.1f}%",
                        "Cap (T)": round(mc_trillion, 1)
                    })

                # Delay kecil agar tidak kena rate limit yfinance
                time.sleep(0.2)

            except Exception:
                continue

        # Selesai scanning
        time.sleep(0.5)
        my_bar.empty()

        # Tampilkan hasil
        if results:
            st.success(f"🎉 {len(results)} saham lolos filter!")
            df_final = pd.DataFrame(results)
            st.dataframe(df_final, use_container_width=True)

            # Download CSV
            csv = df_final.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="idx_swing_scan.csv",
                mime="text/csv"
            )
        else:
            st.warning("Tidak ada saham yang lolos filter saat ini.")

# Footer
st.markdown("---")
st.caption("Data dari yfinance • Update real-time saat scan • Dibuat oleh jamilstempel.com • 23 Jan 2026")
