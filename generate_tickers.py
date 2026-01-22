import pandas as pd

# Fetch dari Wikipedia (update per Jan 2026, ~900+ saham)
url = "https://id.wikipedia.org/wiki/Daftar_perusahaan_yang_tercatat_di_Bursa_Efek_Indonesia"
tables = pd.read_html(url)

tickers = []
for table in tables:
    # Cari kolom 'Kode' (struktur sekarang 1 table besar)
    if 'Kode' in table.columns:
        codes = table['Kode'].dropna().astype(str).str.strip().tolist()
        tickers.extend([code + '.JK' for code in codes if code and len(code) >= 4])  # Filter kode valid

# Hapus duplikat & sort
tickers = sorted(list(set(tickers)))

# Save ke CSV
pd.DataFrame(tickers, columns=['ticker']).to_csv('tickers.csv', index=False)
print(f"Berhasil generate {len(tickers)} ticker! File tickers.csv siap.")
print("Contoh 10 pertama:", tickers[:10])
