"""
scraper_engine.py
Hybrid scraping logic: Serper.dev API + NTB local portal scraper.
No Streamlit dependency — all functions are pure Python.
"""

import difflib
import re
import time
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from fake_useragent import UserAgent

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
KBLI_MAPPING: Dict = {
    "Pertanian": {
        "uraian": "Pertanian, Kehutanan, dan Perikanan",
        "keywords": [
            "panen", "luas tanam", "produksi", "sawah", "padi", "jagung",
            "nelayan", "perikanan", "hortikultura", "cabai", "tomat",
            "tembakau", "sapi", "peternakan ayam", "produksi telur",
        ],
    },
    "Industri Pengolahan": {
        "uraian": "Industri Pengolahan",
        "keywords": [
            "pabrik", "produksi", "UMKM", "olahan", "oven tembakau",
            "tembakau rajang", "industri rokok", "percetakan", "konveksi",
            "kerajinan", "anyaman", "tenun", "rotan", "anyaman ketak",
        ],
    },
    "Perdagangan": {
        "uraian": "Perdagangan Besar dan Eceran; Reparasi Mobil dan Sepeda Motor",
        "keywords": [
            "harga", "pasar", "inflasi", "distribusi", "penjualan motor",
            "penjualan mobil", "kenaikan harga", "pedagang kaki lima",
        ],
    },
    "Pariwisata": {
        "uraian": "Penyediaan Akomodasi dan Makan Minum; Seni, Hiburan, dan Rekreasi",
        "keywords": [
            "hotel", "wisatawan", "destinasi", "jumlah kunjungan", "mandalika",
            "kuta lombok", "MXGP", "tingkat hunian", "resort", "penginapan",
            "villa", "glamping", "turis",
        ],
    },
    "Penyedia Makan Minum": {
        "uraian": "Penyediaan Makan Minum",
        "keywords": ["MBG", "restoran", "rumah makan"],
    },
    "Pendidikan": {
        "uraian": "Pendidikan",
        "keywords": ["UKT", "jumlah siswa", "jumlah guru", "guru PPPK"],
    },
    "Kesehatan": {
        "uraian": "Kesehatan dan Kegiatan Sosial",
        "keywords": [
            "rumah sakit", "klinik", "jumlah pasien",
            "tenaga kesehatan", "tenaga Kesehatan PPPK",
        ],
    },
    "Konstruksi": {
        "uraian": "Konstruksi",
        "keywords": [
            "pembangunan jalan", "pembangunan gedung",
            "pembangunan perumahan", "perumahan", "konstruksi", "instalasi",
        ],
    },
    "Jasa": {
        "uraian": "Jasa Profesional, Ilmiah, dan Teknis; Administrasi Pemerintahan; Jasa Lainnya",
        "keywords": ["arsitek", "event", "konser", "hiburan", "notaris", "pengacara"],
    },
    "Transportasi": {
        "uraian": "Transportasi dan Pergudangan",
        "keywords": [
            "angkutan", "bus", "terminal", "ojek", "pelabuhan",
            "bandara", "pengiriman barang", "logistik", "pergudangan",
        ],
    },
    "Keuangan": {
        "uraian": "Jasa Keuangan dan Asuransi",
        "keywords": [
            "kredit", "pinjaman", "bank", "BPR", "koperasi",
            "asuransi", "dana desa", "investasi", "UMKM modal",
        ],
    },
    "Listrik, Gas, Air": {
        "uraian": "Pengadaan Listrik, Gas, dan Air",
        "keywords": [
            "PLN", "PDAM", "air bersih", "listrik",
            "sambungan listrik", "elektrifikasi", "jaringan gas",
        ],
    },
    "Informasi & Komunikasi": {
        "uraian": "Informasi dan Komunikasi",
        "keywords": [
            "internet", "sinyal", "BTS", "digitalisasi",
            "aplikasi", "media sosial", "e-commerce", "startup",
        ],
    },
}

TRIWULAN_CONFIG: Dict = {
    "T1 2026 (Jan–Mar)": {
        "start": date(2026, 1, 1),
        "end":   date(2026, 3, 31),
        "tbs":   "cdr:1,cd_min:1/1/2026,cd_max:3/31/2026",
        "label": "T1_2026",
    },
    "T2 2026 (Apr–Jun)": {
        "start": date(2026, 4, 1),
        "end":   date(2026, 6, 30),
        "tbs":   "cdr:1,cd_min:4/1/2026,cd_max:6/30/2026",
        "label": "T2_2026",
    },
    "T3 2026 (Jul–Sep)": {
        "start": date(2026, 7, 1),
        "end":   date(2026, 9, 30),
        "tbs":   "cdr:1,cd_min:7/1/2026,cd_max:9/30/2026",
        "label": "T3_2026",
    },
    "T4 2026 (Okt–Des)": {
        "start": date(2026, 10, 1),
        "end":   date(2026, 12, 31),
        "tbs":   "cdr:1,cd_min:10/1/2026,cd_max:12/31/2026",
        "label": "T4_2026",
    },
}

REGIONS: List[str] = ["Lombok Tengah", "Nusa Tenggara Barat"]

LOCAL_PORTALS: List[Dict] = [
    {"name": "Suara NTB",    "search": "https://www.suarantb.com/?s={q}"},
    {"name": "Lombok Post",  "search": "https://lombokpost.jawapos.com/?s={q}"},
    {"name": "Radar Lombok", "search": "https://radarlombok.co.id/?s={q}"},
    {"name": "Koran Lombok", "search": "https://www.koranlombok.id/?s={q}"},
]

_UA = UserAgent()

# ── DATE PARSING — HARD FILTER: year < 2026 → None ───────────────────────────
_REL = re.compile(r"(\d+)\s+(second|minute|hour|day|week|month)s?\s+ago", re.I)
_ID_DATE = re.compile(
    r"(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus"
    r"|september|oktober|november|desember)\s+(\d{4})", re.I,
)
_BULAN_ID: Dict[str, str] = {
    "januari": "1", "februari": "2", "maret": "3",   "april": "4",
    "mei": "5",     "juni": "6",     "juli": "7",     "agustus": "8",
    "september":"9","oktober":"10","november":"11","desember":"12",
}
_UNIT_DAYS: Dict[str, int] = {
    "second": 0, "minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30,
}


def parse_date_strict(raw: str) -> Optional[date]:
    """Return parsed date only if year >= 2026; otherwise None."""
    if not raw:
        return None
    raw = raw.strip()

    m = _REL.match(raw)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        d = date.today() - timedelta(days=n * _UNIT_DAYS.get(unit, 1))
        return d if d.year >= 2026 else None

    m2 = _ID_DATE.search(raw)
    if m2:
        day, bln, yr = m2.groups()
        try:
            d = date(int(yr), int(_BULAN_ID[bln.lower()]), int(day))
            return d if d.year >= 2026 else None
        except ValueError:
            pass

    try:
        d = dateparser.parse(raw, dayfirst=False).date()
        return d if d.year >= 2026 else None
    except Exception:
        return None


# ── DEDUPLICATION WITH DIFFLIB ────────────────────────────────────────────────
def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower().strip())


def _similar(a: str, b: str, threshold: float = 0.82) -> bool:
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold


def deduplicate(rows: List[Dict]) -> List[Dict]:
    unique: List[Dict] = []
    norms: List[str] = []
    for row in rows:
        nt = _norm(row.get("Judul Berita", ""))
        if not any(_similar(nt, x) for x in norms):
            unique.append(row)
            norms.append(nt)
    return unique


# ── KBLI CLASSIFIER ───────────────────────────────────────────────────────────
def classify_kbli(text: str) -> Tuple[str, str]:
    t = text.lower()
    for kat, cfg in KBLI_MAPPING.items():
        for kw in cfg["keywords"]:
            if kw.lower() in t:
                return kat, cfg["uraian"]
    return "Lainnya", "Fenomena ekonomi lainnya"


# ── SERPER API ────────────────────────────────────────────────────────────────
def search_serper(api_key: str, query: str, tbs: str, num: int = 10) -> List[Dict]:
    payload = {"q": query, "num": num, "gl": "id", "hl": "id", "tbs": tbs}
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    r = requests.post(
        "https://google.serper.dev/search",
        headers=headers, json=payload, timeout=20,
    )
    r.raise_for_status()
    return r.json().get("organic", [])


# ── LOCAL PORTAL SCRAPER ──────────────────────────────────────────────────────
def _portal_headers() -> Dict:
    return {
        "User-Agent":      _UA.random,
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }


def _portal_date(el: BeautifulSoup) -> Optional[date]:
    t = el.find("time", attrs={"datetime": True})
    if t:
        d = parse_date_strict(t["datetime"])
        if d:
            return d
    text = el.get_text(" ", strip=True)
    m = _ID_DATE.search(text)
    if m:
        day, bln, yr = m.groups()
        try:
            d = date(int(yr), int(_BULAN_ID[bln.lower()]), int(day))
            return d if d.year >= 2026 else None
        except ValueError:
            pass
    return None


def local_portal_scraper(
    keyword: str,
    region: str,
    start_dt: date,
    end_dt: date,
) -> List[Dict]:
    """Search NTB local portals via BeautifulSoup. Strict 2026 filter enforced."""
    query = f"{region} {keyword}"
    results: List[Dict] = []

    for portal in LOCAL_PORTALS:
        url  = portal["search"].format(q=quote_plus(query))
        base = portal["search"].split("/?")[0]
        try:
            r = requests.get(url, headers=_portal_headers(), timeout=12)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")

            containers = (
                soup.find_all("article")
                or soup.find_all(class_=re.compile(r"post|article|entry", re.I))
                or []
            )

            for art in containers[:6]:
                heading = art.find(["h2", "h3", "h4"])
                if not heading:
                    continue
                a_tag = heading.find("a", href=True)
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                link  = a_tag["href"]
                if not link.startswith("http"):
                    link = base + "/" + link.lstrip("/")

                pub_date = _portal_date(art)
                if not pub_date or pub_date.year != 2026:
                    continue
                if not (start_dt <= pub_date <= end_dt):
                    continue

                snippet_el = art.find(
                    class_=re.compile(r"summary|excerpt|content|desc", re.I)
                )
                snippet = snippet_el.get_text(strip=True)[:300] if snippet_el else ""
                if not snippet:
                    p = art.find("p")
                    snippet = p.get_text(strip=True)[:300] if p else ""

                results.append({
                    "Judul Berita":  title,
                    "Tanggal":       pub_date.strftime("%Y-%m-%d"),
                    "Sumber":        portal["name"],
                    "Kategori KBLI": "",
                    "Uraian KBLI":   "",
                    "Fenomena":      snippet,
                    "Link":          link,
                })
        except Exception:
            continue

    return results


# ── MAIN ORCHESTRATOR ─────────────────────────────────────────────────────────
def run_scrape(
    api_key: str,
    region: str,
    triwulan_key: str,
    kbli_key: str,
    num_results: int,
    use_local: bool,
    on_progress: Optional[Callable] = None,
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Run full hybrid scrape.
    on_progress(step, total, message) called at each step if provided.
    Returns (DataFrame, error_message_or_None).
    """
    cfg      = TRIWULAN_CONFIG[triwulan_key]
    tbs      = cfg["tbs"]
    start_dt = cfg["start"]
    end_dt   = cfg["end"]
    kbli_cfg = KBLI_MAPPING[kbli_key]
    uraian   = kbli_cfg["uraian"]
    keywords = kbli_cfg["keywords"][:5]

    rows: List[Dict] = []
    seen_urls: set = set()
    total = len(keywords) + (1 if use_local else 0)

    def _notify(step: int, msg: str) -> None:
        if on_progress:
            on_progress(step, total, msg)

    # ── Serper queries ────────────────────────────────────────────────────────
    for i, kw in enumerate(keywords):
        query = f"{region} {kw}"
        _notify(i, f"Serper [{i+1}/{len(keywords)}]: **{query}**")

        try:
            items = search_serper(api_key, query, tbs, num=num_results)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code == 401:
                return pd.DataFrame(), "API_KEY_INVALID"
            _notify(i, f"⚠️ HTTP {code} pada query '{kw}' — dilewati.")
            continue
        except Exception as exc:
            _notify(i, f"⚠️ {exc}")
            continue

        for item in items:
            link = item.get("link", "")
            if not link or link in seen_urls:
                continue
            seen_urls.add(link)

            judul    = item.get("title", "").strip()
            snippet  = item.get("snippet", "").strip()
            source   = item.get("source", "")
            raw_date = item.get("date", "")

            pub_date = parse_date_strict(raw_date)
            if pub_date and not (start_dt <= pub_date <= end_dt):
                continue

            tanggal_str = pub_date.strftime("%Y-%m-%d") if pub_date else "—"
            kat, ur = classify_kbli(f"{judul} {snippet}")

            rows.append({
                "Judul Berita":  judul,
                "Tanggal":       tanggal_str,
                "Sumber":        source,
                "Kategori KBLI": kbli_key,
                "Uraian KBLI":   uraian,
                "Fenomena":      snippet,
                "Link":          link,
            })

        time.sleep(0.4)

    # ── Local portal scraper ──────────────────────────────────────────────────
    if use_local:
        _notify(len(keywords), "Scraping portal berita lokal NTB...")
        local_items = local_portal_scraper(
            kbli_cfg["keywords"][0], region, start_dt, end_dt
        )
        for item in local_items:
            link = item.get("Link", "")
            if not link or link in seen_urls:
                continue
            seen_urls.add(link)
            kat, ur = classify_kbli(f"{item['Judul Berita']} {item['Fenomena']}")
            item["Kategori KBLI"] = kbli_key
            item["Uraian KBLI"]   = uraian
            rows.append(item)

    _notify(total, f"Selesai — {len(rows)} berita ditemukan sebelum dedup.")

    rows = deduplicate(rows)

    df = pd.DataFrame(rows)
    if not df.empty:
        df.sort_values("Tanggal", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)

    return df, None
