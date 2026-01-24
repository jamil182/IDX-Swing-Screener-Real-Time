import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
import requests
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="IDX Pro Screener 2026", layout="wide", page_icon="📈")

# Fungsi Kirim Telegram menggunakan Secrets
def send_telegram_msg(message):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Gagal kirim Telegram: {e}")

# --- UI HEADER ---
st.title("🚀 IDX Swing Pro v2026")
st.markdown("Screener otomatis dengan **Risk & Money Management** terintegrasi.")

# --- SIDEBAR ---
st.sidebar.header("🔧 Parameter Filter")
rsi_min = st.sidebar.slider("Min RSI (14)", 0, 100, 50) # Diturunkan ke 50 agar lebih pemaaf
vol_ratio_min = st.sidebar.slider("Min Vol Ratio", 0.0, 5.0, 1.0, 0.1)
mcap_min = st.sidebar.number_input("Min Market Cap (Triliun)", 0.0, 1000.0, 1.0)
pct_1m_min = st.sidebar.slider("Min % 1 Bulan", -20, 100, 0)

st.sidebar.divider()
st.sidebar.header("💰 Money Management")
total_budget = st.sidebar.number_input("Total Modal (Rp)", value=10000000, step=1000000)
risk_per_trade = st.sidebar.slider("Resiko per Trade (%)", 0.1, 5.0, 1.0)
use_telegram = st.sidebar.toggle("Kirim ke Telegram setelah Scan", value=False)

# List Saham (Gunakan list default_stocks yang sudah Anda punya sebelumnya)
# Untuk contoh ini saya singkat, namun Anda bisa memasukkan 800+ saham Anda di sini.
default_stocks = ["AADI", "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "GOTO", "AMMN", "BREN", "BRPT", "ADRO"] 
stocks_to_scan = [f"{s}.JK" for s in default_stocks]

# --- SCANNING LOGIC ---
if st.button("🔍 Jalankan Scanner"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 1. DOWNLOAD DATA MASSAL (OHLCV)
    status_text.text("Mengunduh data pasar (OHLCV)... Harap tunggu.")
    data = yf.download(stocks_to_scan, period="1y", interval="1d", group_by='ticker', progress=False)

    # 2. PROSES SCANNING TEKNIKAL
    for i, ticker in enumerate(stocks_to_scan):
        try:
            # Proteksi jika data ticker tidak ditemukan
            if ticker not in data.columns.levels[0]: continue
            
            df = data[ticker].copy().dropna(subset=['Close'])
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
            
            # Volume & Performance
            vol_today = float(last['Volume'])
            avg_vol = float(df['Volume'].tail(20).mean())
            vol_ratio = vol_today / avg_vol if avg_vol > 0 else 0
            prev_1m = df.iloc[-21]['Close'] if len(df) >= 21 else df.iloc[0]['Close']
            pct_1m = ((price - prev_1m) / prev_1m) * 100

            # Filter Teknikal
            is_uptrend = (price > sma20 > sma200) if sma200 > 0 else (price > sma20)
            
            if is_uptrend and rsi >= rsi_min and vol_ratio >= vol_ratio_min and pct_1m >= pct_1m_min:
                # 3. CEK MARKET CAP HANYA UNTUK YANG LOLOS TEKNIKAL (Efisien!)
                status_text.text(f"Mengecek Market Cap: {ticker}...")
                t_obj = yf.Ticker(ticker)
                mcap = t_obj.info.get('marketCap', 0) / 1e12
                
                if mcap >= mcap_min:
                    # Risk Management
                    sl_price = sma20 * 0.98
                    risk_pct = ((price - sl_price) / price) * 100
                    if risk_pct < 2 or risk_pct > 8: 
                        sl_price = price * 0.95
                        risk_pct = 5.0
                    
                    tp_price = price * (1 + (risk_pct * 2 / 100))
                    
                    # Money Management
                    amt_to_risk = total_budget * (risk_per_trade / 100)
                    lots = int((amt_to_risk / (price - sl_price)) // 100) if (price - sl_price) > 0 else 0
                    total_buy = lots * 100 * price

                    results.append({
                        "Ticker": ticker.replace(".JK", ""),
                        "Price": int(price),
                        "RSI": round(rsi, 1),
                        "Vol Ratio": round(vol_ratio, 2),
                        "SL": int(sl_price),
                        "TP": int(tp_price),
                        "Lot": lots,
                        "Alokasi": int(total_buy),
                        "MCap (T)": round(mcap, 1)
                    })
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_to_scan))

    status_text.empty()
    
    # --- DISPLAY HASIL ---
    if results:
        df_res = pd.DataFrame(results)
        st.success(f"Ditemukan {len(results)} Saham Potensial!")
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        
        if use_telegram:
            msg = f"🚀 *IDX SIGNAL {datetime.now().strftime('%H:%M')}*\n"
            for r in results:
                msg += f"• *{r['Ticker']}*: Rp{r['Price']} | SL:{r['SL']} | TP:{r['TP']} | *{r['Lot']} Lot*\n"
            send_telegram_msg(msg)
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria. Coba turunkan filter di sidebar.")

st.caption(f"© 2026 jamilstempel.com | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
