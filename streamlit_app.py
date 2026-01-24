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
    4. 5% - 10%: Mencari saham yang mulai uptrend.--> 15%: Mencari saham yang sedang dalam fase super-growth.
    5. Safe Swing/Blue&emsp;&emsp;&emsp;:Min RSI (14): 50 ✔&nbsp;&nbsp;&nbsp;Min Volume Today: 1.2 ✔ Min Market Cap: 50 T.&nbsp;&nbsp;✔ Min % Change 1 Bulan:&nbsp; > 3%
    6. Aggressive Swing/Mid Cap : Min RSI (14): 60 ✔ Min Volume Today: 2.00 ✔ Min Market Cap: 2 T.&nbsp;&nbsp;&nbsp;✔ Min % Change 1 Bulan:&nbsp; > 10%
    7. Fast Trade/Scalping&emsp;&emsp;&emsp;: Min RSI (14): 70 ✔ Min Volume Today: 3.00 ✔ Min Market Cap: Bebas. ✔ Min % Change 1 Bulan:&nbsp; > 15%
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
                # 1. Ambil data per ticker
                if total_len == 1:
                    df = data
                else:
                    df = data[ticker]
                
                df = df.dropna(subset=['Close'])
                if len(df) < 200: 
                    continue

                # 2. Hitung Indikator
                df["SMA20"] = ta.sma(df["Close"], length=20)
                df["SMA200"] = ta.sma(df["Close"], length=200)
                df["RSI"] = ta.rsi(df["Close"], length=14)
                
                last = df.iloc[-1]
                prev_1m = df.iloc[-21] if len(df) > 21 else df.iloc[0]
                
                # 3. Ekstrak Nilai Terakhir
                price = float(last['Close'])
                sma20 = float(last['SMA20'])
                sma200 = float(last['SMA200'])
                rsi = float(last['RSI'])
                vol_today = float(last['Volume'])
                avg_vol = float(df['Volume'].tail(20).mean())
                vol_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                pct_1m = ((price - prev_1m['Close']) / prev_1m['Close']) * 100

                # 4. Filter Dasar (Uptrend & Momentum)
                if (price > sma20 > sma200 and rsi >= rsi_min and vol_ratio >= vol_ratio_min):
                    
                    # 5. Ambil Fundamental Data (Market Cap)
                    t_obj = yf.Ticker(ticker)
                    mcap = t_obj.info.get('marketCap', 0) / 1e12
                    
                    if mcap >= mcap_min and pct_1m >= pct_1m_min:
                        
                        # --- LOGIKA RISK MANAGEMENT (Indentasi Diperbaiki) ---
                        # Stop Loss: 2% di bawah SMA20
                        sl_price = sma20 * 0.98  
                        risk_pct = ((price - sl_price) / price) * 100

                        # Proteksi jika SMA20 terlalu dekat/jauh, gunakan default 5%
                        if risk_pct < 2 or risk_pct > 8:
                            sl_price = price * 0.95
                            risk_pct = 5.0

                        # Target Profit: Risk Reward Ratio 1:2
                        reward_pct = risk_pct * 2
                        tp_price = price * (1 + (reward_pct / 100))

                        # 6. Masukkan ke Hasil Final
                        results.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(price),
                            "RSI": round(rsi, 2),
                            "Vol Ratio": round(vol_ratio, 2),
                            "SMA20": int(sma20),
                            "Stop Loss (SL)": int(sl_price),
                            "Target Profit (TP)": int(tp_price),
                            "Risk:Reward": "1:2",
                            "Potensi Profit": f"{reward_pct:.1f}%",
                            "Market Cap (T)": round(mcap, 2)
                        })
            except Exception as e:
                # Log error jika perlu: print(f"Error pada {ticker}: {e}")
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
           "Stop Loss (SL)": st.column_config.NumberColumn("Exit (SL)", format="Rp %d", help="Jual jika harga di bawah ini"),
           "Target Profit (TP)": st.column_config.NumberColumn("Target (TP)", format="Rp %d", help="Area ambil untung"),
           "Potensi Profit": st.column_config.TextColumn("Potensi Untung", help="Estimasi % kenaikan"),
           "Price": st.column_config.NumberColumn("Harga Masuk", format="Rp %d")
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
