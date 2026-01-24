import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="IDX Pro Screener 2026", layout="wide", page_icon="📈")

# Custom CSS untuk tampilan lebih profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🚀 IDX Swing Screener Pro v2026")
st.caption("Advanced Momentum & Trend Scanner | Data via Yahoo Finance (Delayed)")

with st.expander("ℹ️ Cara Penggunaan & Strategi"):
    st.write("""
    1. **Trend Wajib:** Sistem secara otomatis memfilter saham yang berada di atas SMA 200 (Major Trend) dan SMA 20 (Minor Trend).
    2. **Momentum:** Gunakan RSI > 50 untuk mencari saham yang sedang 'panas'.
    3. **Volume:** Volume Ratio > 2 menandakan adanya akumulasi atau minat besar di hari ini dibanding rata-rata 20 hari.
    """)

# --- SIDEBAR: INPUT & FILTER ---
st.sidebar.header("🛠️ Parameter Scan")

uploaded_file = st.sidebar.file_uploader("Upload Excel IDX (Kolom B: Kode)", type=["xlsx"])

# Default list (Contoh singkat, bisa ditambah)
default_stocks = ["BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "AMMN", "BRPT", "BREN"]

if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file, header=None)
        stocks_to_scan = df_upload.iloc[1:, 1].dropna().unique().tolist()
        st.sidebar.success(f"Loaded {len(stocks_to_scan)} saham dari Excel")
    except:
        st.sidebar.error("Gagal baca Excel. Gunakan default.")
        stocks_to_scan = default_stocks
else:
    stocks_to_scan = default_stocks
    st.sidebar.info(f"Mode: Default ({len(stocks_to_scan)} saham)")

# Clean Ticker Format
stocks_to_scan = [f"{str(s).strip().replace('.JK', '')}.JK" for s in stocks_to_scan]

# Filter Sliders
rsi_min = st.sidebar.slider("Min RSI (14)", 0, 100, 55)
vol_ratio_min = st.sidebar.slider("Min Vol Ratio (vs Avg 20d)", 0.0, 5.0, 1.5, 0.1)
mcap_min = st.sidebar.number_input("Min Market Cap (Triliun IDR)", 0.0, 2000.0, 1.0)
pct_1m_min = st.sidebar.slider("Min % Change (1 Bulan)", -30, 100, 5)

# --- LOGIC SCANNING ---
if st.button("🔍 Mulai Pemindaian Massal"):
    results = []
    
    # Progress UI
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Batch download untuk kecepatan tinggi (YFinance mendongkrak performa jika dipanggil sekaligus)
    # Kita bagi per 50 saham agar tidak berat di satu request
    batch_size = 50
    total_len = len(stocks_to_scan)
    
    for i in range(0, total_len, batch_size):
        batch = stocks_to_scan[i:i+batch_size]
        status_text.text(f"Mengunduh Data Batch {i//batch_size + 1}...")
        
        # Download data sekaligus
        try:
            data = yf.download(batch, period="1y", interval="1d", group_by='ticker', progress=False, threads=True)
        except Exception as e:
            st.error(f"Error download batch: {e}")
            continue

        for ticker in batch:
            try:
                # Mengambil DataFrame untuk satu ticker
                if total_len == 1: # Handle yfinance return format
                    df = data
                else:
                    df = data[ticker]
                
                df = df.dropna(subset=['Close'])
                
                if len(df) < 200: continue

                # Kalkulasi Indikator
                df["SMA20"] = ta.sma(df["Close"], length=20)
                df["SMA200"] = ta.sma(df["Close"], length=200)
                df["RSI"] = ta.rsi(df["Close"], length=14)
                
                last = df.iloc[-1]
                prev_1m = df.iloc[-21] if len(df) > 21 else df.iloc[0]
                
                # Data Points
                price = last['Close']
                sma20 = last['SMA20']
                sma200 = last['SMA200']
                rsi = last['RSI']
                vol_today = last['Volume']
                avg_vol = df['Volume'].tail(20).mean()
                vol_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                pct_1m = ((price - prev_1m['Close']) / prev_1m['Close']) * 100

                # Info Market Cap (Cache info untuk efisiensi)
                # Note: Info tetap harus dipanggil per ticker
                t_info = yf.Ticker(ticker).info
                mcap = t_info.get('marketCap', 0) / 1e12

                # --- FILTER LOGIC ---
                if (price > sma20 > sma200 and 
                    rsi >= rsi_min and 
                    vol_ratio >= vol_ratio_min and
                    mcap >= mcap_min and
                    pct_1m >= pct_1m_min):
                    
                    results.append({
                        "Ticker": ticker.replace(".JK", ""),
                        "Price": int(price),
                        "RSI": round(rsi, 2),
                        "Vol Ratio": round(vol_ratio, 2),
                        "Perf 1M": f"{pct_1m:.2f}%",
                        "MCap (T)": round(mcap, 2)
                    })
            except:
                continue
        
        progress_bar.progress((i + batch_size) / total_len if (i + batch_size) < total_len else 1.0)

    status_text.empty()
    progress_bar.empty()

    # --- TAMPILKAN HASIL ---
    if results:
        st.success(f"Ditemukan {len(results)} saham potensial!")
        
        df_res = pd.DataFrame(results)
        
        # Tampilan Grid Metrik (Top 3 Vol Ratio)
        top_vol = df_res.sort_values("Vol Ratio", ascending=False).head(3)
        cols = st.columns(3)
        for idx, row in enumerate(top_vol.to_dict(orient='records')):
            cols[idx].metric(f"🔥 High Vol: {row['Ticker']}", f"Rp{row['Price']}", f"Ratio: {row['Vol Ratio']}")

        st.markdown("---")
        
        # Tabel Interaktif
        st.dataframe(
            df_res, 
            use_container_width=True,
            column_config={
                "Perf 1M": st.column_config.TextColumn("Performa 1 bln"),
                "RSI": st.column_config.ProgressColumn("Momentum RSI", min_value=0, max_value=100, format="%.2f"),
                "Price": st.column_config.NumberColumn("Harga", format="Rp %d")
            }
        )
        
        # Export
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Hasil ke CSV", csv, "idx_scan_result.csv", "text/csv")
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria saat ini. Coba turunkan filter.")

# FOOTER
st.markdown("---")
st.caption(f"© 2026 jamilstempel.com | Terakhir diupdate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
