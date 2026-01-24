import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="IDX Pro Screener 2026", layout="wide", page_icon="📈")

# Fungsi Kirim Telegram menggunakan Secrets
def send_telegram_msg(message):
    try:
        # Nama key disesuaikan dengan standar rapi: TELEGRAM_BOT_TOKEN
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Gagal kirim Telegram: {e}. Pastikan nama di Secrets adalah TELEGRAM_BOT_TOKEN")

# --- UI HEADER ---
st.title("🚀 IDX Swing Pro v2026")
st.markdown("Screener otomatis dengan **Risk & Money Management** terintegrasi.")

# --- SIDEBAR ---
st.sidebar.header("🔧 Parameter Filter")
rsi_min = st.sidebar.slider("Min RSI (14)", 0, 100, 50)
vol_ratio_min = st.sidebar.slider("Min Vol Ratio", 0.0, 5.0, 1.2, 0.1)
mcap_min = st.sidebar.number_input("Min Market Cap (Triliun)", 0.0, 1000.0, 1.0)
pct_1m_min = st.sidebar.slider("Min % 1 Bulan", -20, 100, 0)

st.sidebar.divider()
st.sidebar.header("💰 Money Management")
total_budget = st.sidebar.number_input("Total Modal (Rp)", value=10000000, step=1000000)
risk_per_trade = st.sidebar.slider("Resiko per Trade (%)", 0.1, 5.0, 1.0)
use_telegram = st.sidebar.toggle("Kirim ke Telegram setelah Scan", value=True)

# List Saham (Sudah pakai .JK, tidak perlu ditambah lagi nanti)
default_stocks = ["AADI.JK", "AALI.JK", "ABMM.JK", "ACES.JK", "ADMR.JK", "ADRO.JK", "AMMN.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRIS.JK", "BRPT.JK", "BREN.JK", "GOTO.JK", "TLKM.JK", "UNTR.JK"]

# --- SCANNING LOGIC ---
if st.button("🔍 Jalankan Scanner Sekarang"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Download Massal
    status_text.info("Mengunduh data pasar... Harap tunggu.")
    data = yf.download(default_stocks, period="1y", interval="1d", group_by='ticker', progress=False)

    for i, ticker in enumerate(default_stocks):
        try:
            if ticker not in data.columns.levels[0]: continue
            
            df = data[ticker].copy().dropna(subset=['Close'])
            if len(df) < 20: continue

            # Indikator
            df["SMA20"] = ta.sma(df["Close"], length=20)
            df["SMA200"] = ta.sma(df["Close"], length=200)
            df["RSI"] = ta.rsi(df["Close"], length=14)
            df.fillna(0, inplace=True)
            
            last = df.iloc[-1]
            price = float(last['Close'])
            sma20 = float(last['SMA20'])
            sma200 = float(last['SMA200'])
            rsi = float(last['RSI'])
            
            vol_ratio = float(last['Volume']) / df['Volume'].tail(20).mean()
            prev_close_1m = df.iloc[-21]['Close'] if len(df) >= 21 else df.iloc[0]['Close']
            pct_1m = ((price - prev_close_1m) / prev_close_1m) * 100

            # Filter Uptrend
            is_uptrend = (price > sma20 > sma200) if sma200 > 0 else (price > sma20)
            
            if is_uptrend and rsi >= rsi_min and vol_ratio >= vol_ratio_min and pct_1m >= pct_1m_min:
                # Ambil Info Fundamental (Hanya untuk yang lolos teknikal)
                t_info = yf.Ticker(ticker).info
                mcap = t_info.get('marketCap', 0) / 1e12
                
                if mcap >= mcap_min:
                    # Risk Management
                    sl_price = sma20 * 0.98
                    risk_per_sh = price - sl_price
                    if risk_per_sh / price < 0.02: 
                        sl_price = price * 0.95
                        risk_per_sh = price - sl_price
                    
                    tp_price = price + (risk_per_sh * 2)
                    
                    # Position Sizing
                    amt_to_risk = total_budget * (risk_per_trade / 100)
                    lots = int((amt_to_risk / risk_per_sh) // 100) if risk_per_sh > 0 else 0
                    total_buy = lots * 100 * price

                    results.append({
                        "Ticker": ticker.replace(".JK", ""),
                        "Price": int(price),
                        "RSI": round(rsi, 1),
                        "Vol Ratio": round(vol_ratio, 2),
                        "SL": int(sl_price),
                        "TP": int(tp_price),
                        "Lot": lots,
                        "Alokasi": f"Rp {int(total_buy):,}",
                        "MCap (T)": round(mcap, 1)
                    })
        except:
            continue
        progress_bar.progress((i + 1) / len(default_stocks))

    status_text.empty()

    if results:
        df_res = pd.DataFrame(results)
        st.success(f"✅ Ditemukan {len(results)} Saham Potensial!")
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        
        if use_telegram:
            msg = f"🚀 *IDX PRO SIGNAL - {datetime.now().strftime('%H:%M')}*\n"
            for r in results:
                msg += f"• *{r['Ticker']}*: Rp{r['Price']} | SL:{r['SL']} | TP:{r['TP']} | *{r['Lot']} Lot*\n"
            send_telegram_msg(msg)
            st.toast("Notifikasi Telegram Terkirim!")
    else:
        st.warning("Tidak ada saham yang memenuhi kriteria.")

st.caption(f"© 2026 jamilstempel.com | Update: {datetime.now().strftime('%H:%M')}")
