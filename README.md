# 📰 Dasbor Pantauan Berita Ekonomi — PDRB NTB 2026

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Aplikasi dasbor berbasis Streamlit untuk mengambil, mengklasifikasikan, dan menganalisis berita ekonomi sebagai bahan pendukung penyusunan **PDRB Kabupaten/Kota di Provinsi Nusa Tenggara Barat** tahun **2026**.

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|-------|-----------|
| 🔍 **Hybrid Scraping** | Serper.dev (Google Search API) + 6 portal berita lokal NTB |
| 📅 **Filter Triwulan** | T1–T4 2026, filter ketat: berita tahun < 2026 otomatis dibuang |
| 📊 **Klasifikasi KBLI** | 13 lapangan usaha — Pertanian, Pariwisata, Konstruksi, Keuangan, dll |
| 🗑️ **Deduplication** | `difflib.SequenceMatcher` (threshold 82%) — artikel duplikat dihapus |
| 📰 **Umpan Berita** | Tampilan kartu berita dengan tag KBLI berwarna |
| 📤 **Export** | Unduh hasil sebagai Excel (`.xlsx`) atau CSV |

---

## 🗂️ Struktur File

```
webscrap_berita/
├── app.py                        # Antarmuka Streamlit (UI & komponen)
├── scraper_engine.py             # Logika scraping & klasifikasi KBLI
├── requirements.txt              # Daftar dependensi Python
├── .gitignore                    # File sensitif & output tidak di-push
├── README.md                     # Dokumentasi ini
└── .streamlit/
    └── secrets.toml.example      # Template konfigurasi API Key
```

> **Tidak di-commit:** `.env`, `.streamlit/secrets.toml`, `output/`, `*.xlsx`, `*.csv`

---

## 🌐 Cakupan Wilayah

Mendukung seluruh kabupaten/kota di Provinsi NTB:
Lombok Tengah · Lombok Barat · Lombok Timur · Lombok Utara · Kota Mataram · Sumbawa · Sumbawa Barat · Dompu · Bima · Kota Bima

---

## 📡 Sumber Data

**Google Search via Serper.dev API**
- Hasil terfilter otomatis sesuai triwulan via parameter `tbs`

**Portal Berita Lokal NTB**
- Inside Lombok
- NTB Satu
- Post Kota NTB
- Kanal NTB
- Talikanews
- Portal Resmi Pemkab Lombok Tengah

---

## ⚙️ Setup Lokal

```bash
# 1. Clone repo
git clone https://github.com/jadiinaja/webscrap_berita.git
cd webscrap_berita

# 2. Install dependensi
pip install -r requirements.txt

# 3. Konfigurasi API Key
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml → isi SERPER_API_KEY dengan key Anda

# 4. Jalankan
streamlit run app.py
```

> 🔑 Dapatkan API Key gratis di [serper.dev](https://serper.dev)

---

## 🚀 Deploy ke Streamlit Cloud

1. Push repo ke GitHub (`git push origin main`)
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Pilih repo `jadiinaja/webscrap_berita` · branch `main` · file `app.py`
4. Masuk ke **Settings → Secrets**, tambahkan:

```toml
SERPER_API_KEY = "your_serper_api_key_here"
```

5. Klik **Deploy** ✅

---

## 🔧 Catatan Teknis

| Aspek | Detail |
|-------|--------|
| Filter tahun | `parse_date_strict()` — buang berita dengan tahun < 2026 |
| Deduplication | `difflib.SequenceMatcher`, threshold 82% |
| Anti-bot | `fake_useragent`, delay acak, session warm-up per domain |
| Python | 3.9+ (kompatibel Streamlit Cloud) |
| Secrets | `st.secrets` — tidak ada API key yang di-hardcode |

---

## 📋 Kredit

Dikembangkan untuk kebutuhan internal **BPS Kabupaten Lombok Tengah**  
Pendukung penyusunan PDRB Provinsi Nusa Tenggara Barat · 2026
