# 📰 Scraper Berita Ekonomi — PDRB Lombok Tengah

Aplikasi Streamlit untuk mengambil dan mengklasifikasikan berita ekonomi sebagai bahan pendukung penyusunan **PDRB Kabupaten Lombok Tengah** tahun **2026**.

## Fitur

- **Hybrid Scraping**: Serper.dev (Google Search API) + portal berita lokal NTB (Suara NTB, Lombok Post, Radar Lombok, Koran Lombok)
- **Filter Triwulan**: T1–T4 2026 dengan filter tanggal ketat (tahun < 2026 otomatis dibuang)
- **Klasifikasi KBLI Otomatis**: 13 lapangan usaha sesuai KBLI — Pertanian, Industri Pengolahan, Pariwisata, Konstruksi, dan lainnya
- **Deduplication Cerdas**: Artikel serupa dibuang menggunakan `difflib.SequenceMatcher`
- **Export**: Download hasil sebagai Excel (`.xlsx`) atau CSV

## Struktur File

```
├── app.py               # Antarmuka Streamlit (UI)
├── scraper_engine.py    # Logika scraping & klasifikasi (tanpa dependensi Streamlit)
├── requirements.txt     # Daftar library Python
├── .gitignore           # File/folder yang tidak di-push ke GitHub
└── .streamlit/
    └── secrets.toml     # API Key (lokal saja, tidak di-commit)
```

## Setup Lokal

```bash
# 1. Clone repo
git clone https://github.com/jadiinaja/webscrap_berita.git
cd webscrap_berita

# 2. Install dependencies
pip install -r requirements.txt

# 3. Buat file secrets untuk API key
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
SERPER_API_KEY = "isi_api_key_anda_di_sini"
EOF

# 4. Jalankan aplikasi
streamlit run app.py
```

> Dapatkan API Key Serper.dev gratis di: https://serper.dev

## Deploy ke Streamlit Cloud

1. Push repo ke GitHub (lihat perintah Git di bawah)
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Pilih repo `jadiinaja/webscrap_berita`, branch `main`, file `app.py`
4. Di tab **Settings → Secrets**, tambahkan:

```toml
SERPER_API_KEY = "isi_api_key_anda_di_sini"
```

5. Klik **Deploy**

## Perintah Git (First-time Push)

```bash
cd /path/to/scrap_berita

git init
git add app.py scraper_engine.py requirements.txt .gitignore README.md
git commit -m "feat: initial deployment — News Scraper PDRB Lombok Tengah 2026"

git remote add origin https://github.com/jadiinaja/webscrap_berita.git
git branch -M main
git push -u origin main
```

## Catatan Teknis

| Hal | Detail |
|-----|--------|
| Filter tahun | Berita tahun < 2026 dibuang secara ketat di `parse_date_strict()` |
| Deduplication | `difflib.SequenceMatcher` threshold 82% |
| Anti-bot | `fake_useragent`, delay acak, session warm-up (local scraper) |
| Python | 3.9+ (kompatibel dengan Streamlit Cloud) |

## Kredit

Dikembangkan untuk **BPS Kabupaten Lombok Tengah** — Pendukung penyusunan PDRB 2026.
