import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from datetime import datetime

# --- CONFIG HALAMAN ---
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
        st.error(f"Gagal kirim Telegram: {e}. Cek pengaturan Secrets Anda.")

# --- UI HEADER ---
st.title("🚀 IDX Swing Pro v2026")
st.markdown("Screener otomatis dengan **Risk & Money Management** terintegrasi.")

# --- SIDEBAR PARAMETERS ---
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

# Daftar Saham (Disingkat untuk contoh, silakan gunakan list lengkap Anda)
default_stocks = ["AADI.JK", "AALI.JK", "ABMM.JK", "ACES.JK", "ADMR.JK", "ADRO.JK", "AMMN.JK", "ANTM.JK", "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BRIS.JK", "BRPT.JK", "BREN.JK", "GOTO.JK", "TLKM.JK", "UNTR.JK"]

# --- LOGIKA SCANNING ---
if st.button("🔍 Jalankan Scanner Sekarang"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # BATCH PROCESSING: Kita bagi 50 saham per batch agar tidak timeout
    batch_size = 50
    total_stocks = len(default_stocks)
    
    for i in range(0, total_stocks, batch_size):
        batch = default_stocks[i : i + batch_size]
        status_text.info(f"⏳ Mengunduh Batch {i//batch_size + 1}...")
        
        try:
            # Download data OHLCV sekaligus
            data = yf.download(batch, period="1y", interval="1d", group_by='ticker', progress=False, timeout=30)
        except Exception as e:
            st.warning(f"Gagal mengunduh batch {i}: {e}")
            continue

        for ticker in batch:
            try:
                # Proteksi data kosong
                if ticker not in data.columns.levels[0]: continue
                
                df = data[ticker].dropna(subset=['Close'])
                if len(df) < 20: continue

                # Kalkulasi Indikator
                df["SMA20"] = ta.sma(df["Close"], length=20)
                df["SMA200"] = ta.sma(df["Close"], length=200)
                df["RSI"] = ta.rsi(df["Close"], length=14)
                df.fillna(0, inplace=True)
                
                last = df.iloc[-1]
                price = float(last['Close'])
                sma20 = float(last['SMA20'])
                sma200 = float(last['SMA200'])
                rsi = float(last['RSI'])
                
                # Volume & Performa
                vol_today = float(last['Volume'])
                avg_vol = float(df['Volume'].tail(20).mean())
                vol_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                
                prev_1m_idx = -21 if len(df) >= 21 else 0
                prev_price_1m = df.iloc[prev_1m_idx]['Close']
                pct_1m = ((price - prev_price_1m) / prev_price_1m) * 100

                # --- FILTER TEKNIKAL ---
                # Syarat: Harga > SMA20, RSI & Vol sesuai filter
                if price > sma20 and rsi >= rsi_min and vol_ratio >= vol_ratio_min and pct_1m >= pct_1m_min:
                    
                    # Cek Fundamental (Market Cap) - Hanya untuk yang lolos teknikal (Hemat waktu!)
                    t_info = yf.Ticker(ticker).info
                    mcap = t_info.get('marketCap', 0) / 1e12
                    
                    if mcap >= mcap_min:
                        # Risk Management
                        sl_price = sma20 * 0.98
                        risk_per_sh = price - sl_price
                        
                        # Jika SMA20 terlalu dekat, gunakan standar 5%
                        if risk_per_sh / price < 0.02:
                            sl_price = price * 0.95
                            risk_per_sh = price - sl_price
                            
                        tp_price = price + (risk_per_sh * 2) # Reward 1:2
                        
                        # Money Management
                        amt_risk = total_budget * (risk_per_trade / 100)
                        lots = int((amt_risk / risk_per_sh) // 100) if risk_per_sh > 0 else 0
                        alokasi_dana = lots * 100 * price

                        results.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(price),
                            "RSI": round(rsi, 1),
                            "Vol Ratio": round(vol_ratio, 2),
                            "SL": int(sl_price),
                            "TP": int(tp_price),
                            "Lot": lots,
                            "Alokasi": f"Rp {int(alokasi_dana):,}",
                            "MCap (T)": round(mcap, 1)
                        })
            except:
                continue
        
        # Update Progress
        progress_val = min((i + batch_size) / total_stocks, 1.0)
        progress_bar.progress(progress_val)

    status_text.empty()

    # --- TAMPILKAN HASIL ---
    if results:
        df_res = pd.DataFrame(results)
        st.success(f"✅ Berhasil! Ditemukan {len(results)} saham potensial.")
        
        # Tabel Interaktif
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        
        # Kirim Telegram
        if use_telegram:
            msg = f"🚀 *IDX SIGNAL PRO - {datetime.now().strftime('%H:%M')}*\n"
            msg += "--------------------------------\n"
            for r in results:
                msg += f"✅ *{r['Ticker']}*\nPrice: {r['Price']} | RSI: {r['RSI']}\nTarget (TP): {r['TP']} | SL: {r['SL']}\n*Saran: {r['Lot']} Lot*\n\n"
            
            send_telegram_msg(msg)
            st.toast("Notifikasi Telegram Terkirim!")
    else:
        st.warning("⚠️ Tidak ada saham memenuhi kriteria. Coba turunkan filter RSI atau Vol Ratio.")

# --- FOOTER ---
st.divider()
st.caption(f"Data delayed by Yahoo Finance | Update: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | jamilstempel.com")
