import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="IDX Pro Screener 2026", layout="wide", page_icon="📈")

# Fungsi Kirim Telegram menggunakan Secrets
def send_telegram_msg(message):
    try:
        # Pastikan di Streamlit Cloud Secrets namanya: TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Gagal kirim Telegram: {e}. Periksa kembali Secrets Anda.")

# --- UI HEADER ---
st.title("🚀 IDX Swing Screener Pro v2026")
st.caption("Advanced Momentum & Trend Scanner | Money Management & Telegram Integrated")

with st.expander("⚙️ Cara Penggunaan & Strategi"):
    st.write("""
    1. 💡**Trend Wajib:** Harga > SMA 20 (Minor Trend). Jika tersedia, Harga juga harus > SMA 200.
    2. 💡**Momentum:** RSI > 50 menandakan kekuatan pembeli.
    3. 💡**Money Management:** Lot dihitung berdasarkan jarak ke Stop Loss (SL). Semakin jauh SL, semakin sedikit Lot yang disarankan.
    """)

# --- SIDEBAR: INPUT & FILTER ---
st.sidebar.header("🛠️ Parameter Scan")

uploaded_file = st.sidebar.file_uploader("Upload Excel IDX (Kolom B: Kode)", type=["xlsx"])

# Filter Sliders
rsi_min = st.sidebar.slider("Min RSI (14)", 0, 100, 50)
vol_ratio_min = st.sidebar.slider("Min Vol Ratio", 0.0, 5.0, 1.2, 0.1)
mcap_min = st.sidebar.number_input("Min Market Cap (Triliun IDR)", 0.0, 2000.0, 1.0)
pct_1m_min = st.sidebar.slider("Min % Change (1 Bulan)", -30, 100, 0)

st.sidebar.divider()
st.sidebar.header("💰 Money Management")
total_budget = st.sidebar.number_input("Total Modal (Rp)", value=10000000, step=1000000)
risk_per_trade = st.sidebar.slider("Resiko per Trade (%)", 0.1, 5.0, 1.0, help="Berapa % modal yang siap hilang jika kena SL")
use_telegram = st.sidebar.toggle("Kirim ke Telegram setelah Scan", value=True)

# List Saham Default (800+ Tickers)
default_stocks = ["AADI.JK", "AALI.JK", "ABBA.JK", "ABDA.JK", "ABMM.JK", "ACES.JK", "ADRO.JK", "AMMN.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRIS.JK", "BREN.JK", "GOTO.JK", "TLKM.JK"] # ... (Gunakan list lengkap Anda di sini)

if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file, header=None)
        stocks_to_scan = df_upload.iloc[1:, 1].dropna().unique().tolist()
    except:
        stocks_to_scan = default_stocks
else:
    stocks_to_scan = default_stocks

# Clean Ticker Format
stocks_to_scan = [f"{str(s).strip().replace('.JK', '')}.JK" for s in stocks_to_scan]

# --- LOGIC SCANNING ---
if st.button("🔍 Mulai Pemindaian Massal"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    batch_size = 50
    total_len = len(stocks_to_scan)
    
    for i in range(0, total_len, batch_size):
        batch = stocks_to_scan[i:i+batch_size]
        status_text.text(f"Scanning Batch {i//batch_size + 1}...")
        
        try:
            data = yf.download(batch, period="1y", interval="1d", group_by='ticker', progress=False, threads=True)
        except: continue

        for ticker in batch:
            try:
                df = data[ticker].dropna(subset=['Close'])
                if len(df) < 20: continue

                # Hitung Indikator
                df["SMA20"] = ta.sma(df["Close"], length=20)
                df["SMA200"] = ta.sma(df["Close"], length=200)
                df["RSI"] = ta.rsi(df["Close"], length=14)
                df.fillna(0, inplace=True)
                
                last = df.iloc[-1]
                price = float(last['Close'])
                sma20 = float(last['SMA20'])
                sma200 = float(last['SMA200'])
                rsi = float(last['RSI'])
                
                vol_ratio = float(last['Volume']) / df['Volume'].tail(20).mean() if df['Volume'].tail(20).mean() > 0 else 0
                prev_1m = df.iloc[-21]['Close'] if len(df) >= 21 else df.iloc[0]['Close']
                pct_1m = ((price - prev_1m) / prev_1m) * 100

                # Filter Trend & Momentum
                is_uptrend = (price > sma20 > sma200) if sma200 > 0 else (price > sma20)
                
                if is_uptrend and rsi >= rsi_min and vol_ratio >= vol_ratio_min and pct_1m >= pct_1m_min:
                    
                    # Ambil Market Cap (Hanya untuk yang lolos teknikal agar cepat)
                    t_info = yf.Ticker(ticker).info
                    mcap = t_info.get('marketCap', 0) / 1e12
                    
                    if mcap >= mcap_min:
                        # --- RISK & MONEY MANAGEMENT ---
                        sl_price = sma20 * 0.98
                        risk_per_sh = price - sl_price
                        
                        # Proteksi jika SL terlalu dekat/jauh
                        if risk_per_sh / price < 0.02 or risk_per_sh / price > 0.10:
                            sl_price = price * 0.95
                            risk_per_sh = price - sl_price
                            
                        tp_price = price + (risk_per_sh * 2) # Reward 1:2
                        
                        # Kalkulasi Lot
                        amt_to_risk = total_budget * (risk_per_trade / 100)
                        lots = int((amt_to_risk / risk_per_sh) // 100) if risk_per_sh > 0 else 0
                        
                        # Jangan beli lebih dari budget
                        if (lots * 100 * price) > total_budget:
                            lots = int(total_budget // (100 * price))

                        results.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(price),
                            "RSI": round(rsi, 1),
                            "Vol Ratio": round(vol_ratio, 2),
                            "SL": int(sl_price),
                            "TP": int(tp_price),
                            "Lot": lots,
                            "Alokasi": f"Rp {int(lots * 100 * price):,}",
                            "MCap (T)": round(mcap, 1)
                        })
            except: continue
        
        progress_bar.progress(min((i + batch_size) / total_len, 1.0))

    status_text.empty()
    progress_bar.empty()

    if results:
        st.success(f"Ditemukan {len(results)} saham potensial!")
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        
        if use_telegram:
            msg = f"🚀 *IDX SIGNAL PRO v2026*\n"
            msg += f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            msg += "--------------------------------\n"
            for r in results:
                msg += f"✅ *{r['Ticker']}*\nPrice: {r['Price']} | RSI: {r['RSI']}\nTP: {r['TP']} | SL: {r['SL']}\n*Saran: {r['Lot']} Lot*\n\n"
            send_telegram_msg(msg)
            st.toast("Telegram Sent!")
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria. Coba turunkan filter RSI atau Volume.")

st.divider()
st.caption(f"© 2026 jamilstempel.com | Data via Yahoo Finance")
