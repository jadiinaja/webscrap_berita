"""
app.py — Dasbor Pantauan Berita Ekonomi
Premium Streamlit dashboard for webscrap_berita · BPS Kabupaten Lombok Tengah
"""

import html as _html
import re
from datetime import datetime
from io import BytesIO
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scraper_engine import KBLI_MAPPING, PDRB_COMPONENTS, REGIONS, TRIWULAN_CONFIG, run_scrape

# ── API KEY ───────────────────────────────────────────────────────────────────
try:
    SERPER_API_KEY: str = st.secrets["SERPER_API_KEY"]
except (KeyError, FileNotFoundError):
    SERPER_API_KEY = ""

# ── KBLI TAG COLORS ───────────────────────────────────────────────────────────
KBLI_COLORS: Dict[str, str] = {
    "Pertanian":              "#059669",
    "Industri Pengolahan":    "#7C3AED",
    "Perdagangan":            "#D97706",
    "Pariwisata":             "#0891B2",
    "Penyedia Makan Minum":   "#EA580C",
    "Pendidikan":             "#6366F1",
    "Kesehatan":              "#DC2626",
    "Konstruksi":             "#92400E",
    "Jasa":                   "#4338CA",
    "Transportasi":           "#0E7490",
    "Keuangan":               "#065F46",
    "Listrik, Gas, Air":      "#B45309",
    "Informasi & Komunikasi": "#5B21B6",
    "Lainnya":                "#6B7280",
}

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BPS Intelligence Hub",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS — PREMIUM DASHBOARD THEME
# ══════════════════════════════════════════════════════════════════════════════
def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Font ─────────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');
        html, body, [class*="css"], * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        /* ── Hide Streamlit chrome ─────────────────────────────────── */
        #MainMenu                           { visibility: hidden !important; }
        footer                              { visibility: hidden !important; }
        [data-testid="stToolbar"]           { display: none !important; }
        [data-testid="stDecoration"]        { display: none !important; }
        [data-testid="stStatusWidget"]      { display: none !important; }
        section[data-testid="stSidebar"]    { display: none !important; }
        [data-testid="collapsedControl"]    { display: none !important; }

        /* ── Animated dark mesh background ─────────────────────────── */
        .stApp {
            background:
                radial-gradient(ellipse 80% 60% at 20% 10%, rgba(59,130,246,0.18) 0%, transparent 60%),
                radial-gradient(ellipse 60% 50% at 80% 80%, rgba(139,92,246,0.14) 0%, transparent 55%),
                radial-gradient(ellipse 50% 40% at 60% 30%, rgba(16,185,129,0.07) 0%, transparent 50%),
                linear-gradient(160deg, #060918 0%, #0d1229 45%, #0a0f24 100%);
            min-height: 100vh;
        }
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        .block-container {
            padding: 1.75rem 2.25rem 5rem 2.25rem;
            max-width: 1320px;
        }

        /* ── Glass mixin base ───────────────────────────────────────── */
        .glass {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(24px) saturate(150%);
            -webkit-backdrop-filter: blur(24px) saturate(150%);
            border: 1px solid rgba(255,255,255,0.10);
        }

        /* ── App header card ───────────────────────────────────────── */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            padding: 22px 28px;
            margin-bottom: 20px;
            box-shadow:
                0 0 0 1px rgba(59,130,246,0.15) inset,
                0 8px 32px rgba(0,0,0,0.35),
                0 0 60px rgba(59,130,246,0.06);
            position: relative; overflow: hidden;
        }
        .app-header::before {
            content: '';
            position: absolute; inset: 0;
            background: linear-gradient(135deg, rgba(59,130,246,0.06) 0%, transparent 60%);
            pointer-events: none;
        }
        .app-header-left { display: flex; align-items: center; gap: 18px; position: relative; z-index: 1; }
        .app-icon-wrap {
            font-size: 34px;
            background: linear-gradient(135deg, rgba(59,130,246,0.25) 0%, rgba(139,92,246,0.25) 100%);
            border: 1px solid rgba(59,130,246,0.3);
            border-radius: 16px;
            width: 62px; height: 62px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 0 20px rgba(59,130,246,0.2);
        }
        .app-title {
            font-size: 21px; font-weight: 800;
            color: #F1F5F9; margin: 0; line-height: 1.2;
            letter-spacing: -0.02em;
        }
        .app-subtitle {
            font-size: 13px; color: rgba(241,245,249,0.5);
            margin: 4px 0 0; font-weight: 400;
        }
        .live-badge {
            display: inline-flex; align-items: center; gap: 7px;
            background: rgba(16,185,129,0.12);
            border: 1px solid rgba(16,185,129,0.30);
            border-radius: 20px; padding: 6px 14px;
            font-size: 12px; font-weight: 600; color: #34D399;
            box-shadow: 0 0 16px rgba(16,185,129,0.15);
        }
        .live-dot {
            width: 7px; height: 7px; background: #34D399;
            border-radius: 50%; animation: pulse 2s infinite;
            box-shadow: 0 0 8px rgba(52,211,153,0.8);
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50%       { opacity: 0.4; transform: scale(0.8); }
        }

        /* ── Filter section ────────────────────────────────────────── */
        .filter-wrap {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(20px) saturate(150%);
            -webkit-backdrop-filter: blur(20px) saturate(150%);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 16px;
            padding: 22px 24px 18px 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .section-eyebrow {
            font-size: 10px; font-weight: 700;
            color: rgba(241,245,249,0.45);
            text-transform: uppercase; letter-spacing: 0.14em;
            margin-bottom: 14px;
        }

        /* ── KPI cards ─────────────────────────────────────────────── */
        .kpi-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px) saturate(160%);
            -webkit-backdrop-filter: blur(20px) saturate(160%);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 22px 24px;
            flex: 1;
            position: relative; overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 0 30px rgba(59,130,246,0.18);
        }
        .kpi-card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent 0%, var(--kpi-color, #3B82F6) 50%, transparent 100%);
            border-radius: 18px 18px 0 0;
        }
        .kpi-card::after {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at top left, rgba(59,130,246,0.07) 0%, transparent 70%);
            pointer-events: none;
        }
        .kpi-icon  { font-size: 28px; margin-bottom: 10px; display: block; position: relative; z-index: 1; }
        .kpi-label {
            font-size: 10px; font-weight: 700;
            color: rgba(241,245,249,0.45);
            text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 5px;
            position: relative; z-index: 1;
        }
        .kpi-value {
            font-size: 28px; font-weight: 800; color: #F1F5F9;
            line-height: 1.1; position: relative; z-index: 1;
            letter-spacing: -0.02em;
        }
        .kpi-sub   { font-size: 11px; color: rgba(241,245,249,0.4); margin-top: 4px; position: relative; z-index: 1; }

        /* ── Thin progress bar ─────────────────────────────────────── */
        .prog-wrap {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }
        .prog-header {
            display: flex; justify-content: space-between; margin-bottom: 10px;
        }
        .prog-msg  { font-size: 13px; color: rgba(241,245,249,0.75); }
        .prog-pct  { font-size: 13px; font-weight: 700; color: #60A5FA; }
        .prog-track {
            background: rgba(255,255,255,0.08);
            border-radius: 9999px; height: 5px; overflow: hidden;
        }
        .prog-fill {
            height: 100%; border-radius: 9999px;
            background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #06B6D4 100%);
            box-shadow: 0 0 12px rgba(59,130,246,0.6);
            transition: width 0.4s ease;
        }

        /* ── News feed cards ───────────────────────────────────────── */
        .news-card {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(20px) saturate(150%);
            -webkit-backdrop-filter: blur(20px) saturate(150%);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 16px;
            padding: 20px 22px;
            margin-bottom: 12px;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }
        .news-card:hover {
            transform: translateY(-1px);
            border-color: rgba(59,130,246,0.3);
            box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 0 20px rgba(59,130,246,0.08);
        }
        .news-meta {
            display: flex; align-items: center;
            gap: 10px; margin-bottom: 9px; flex-wrap: wrap;
        }
        .kbli-tag {
            font-size: 11px; font-weight: 600;
            padding: 3px 10px; border-radius: 20px;
        }
        .news-date, .news-src {
            font-size: 12px; color: rgba(241,245,249,0.4);
        }
        .news-src { font-weight: 500; color: rgba(241,245,249,0.5); }
        .news-title {
            font-size: 15px; font-weight: 700; color: #F1F5F9;
            margin: 0 0 7px; line-height: 1.5;
        }
        .news-snippet {
            font-size: 13px; color: rgba(241,245,249,0.55); line-height: 1.7;
            margin-bottom: 13px;
        }
        .news-link {
            font-size: 13px; font-weight: 600; color: #60A5FA;
            text-decoration: none;
        }
        .news-link:hover { color: #93C5FD; text-decoration: underline; }
        .news-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 0 0 12px; }

        /* ── Empty state ───────────────────────────────────────────── */
        .empty-state {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px dashed rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 72px 40px;
            text-align: center;
        }
        .empty-icon  { font-size: 60px; margin-bottom: 18px; filter: drop-shadow(0 0 12px rgba(59,130,246,0.3)); }
        .empty-title { font-size: 20px; font-weight: 700; color: #F1F5F9; margin-bottom: 8px; }
        .empty-desc  {
            font-size: 14px; color: rgba(241,245,249,0.5); max-width: 360px;
            margin: 0 auto 22px; line-height: 1.65;
        }
        .empty-cta {
            display: inline-flex; align-items: center; gap: 7px;
            background: rgba(59,130,246,0.12);
            color: #60A5FA;
            border: 1px solid rgba(59,130,246,0.30);
            border-radius: 10px; padding: 10px 20px;
            font-size: 13px; font-weight: 600;
            box-shadow: 0 0 20px rgba(59,130,246,0.12);
        }

        /* ── Primary Button ────────────────────────────────────────── */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%) !important;
            border: 1px solid rgba(59,130,246,0.4) !important;
            border-radius: 12px !important;
            font-weight: 600 !important; font-size: 14px !important;
            color: white !important; width: 100% !important;
            padding: 0.65rem 1.2rem !important;
            box-shadow: 0 4px 15px rgba(37,99,235,0.4), 0 0 30px rgba(79,70,229,0.15) !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.01em !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1D4ED8 0%, #4338CA 100%) !important;
            box-shadow: 0 8px 25px rgba(37,99,235,0.5), 0 0 40px rgba(79,70,229,0.2) !important;
            transform: translateY(-2px) !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 10px !important;
            color: rgba(241,245,249,0.8) !important;
            font-weight: 500 !important;
            transition: all 0.15s !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            background: rgba(255,255,255,0.10) !important;
            border-color: rgba(59,130,246,0.35) !important;
            color: #60A5FA !important;
        }
        .stDownloadButton > button {
            border-radius: 10px !important; font-weight: 500 !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            background: rgba(255,255,255,0.05) !important;
            color: rgba(241,245,249,0.8) !important;
            transition: all 0.15s !important;
            backdrop-filter: blur(10px) !important;
        }
        .stDownloadButton > button:hover {
            border-color: rgba(59,130,246,0.4) !important;
            color: #60A5FA !important;
            background: rgba(59,130,246,0.08) !important;
            box-shadow: 0 0 20px rgba(59,130,246,0.15) !important;
        }

        /* ── Tabs ──────────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(16px);
            border-radius: 12px; padding: 4px;
            border: 1px solid rgba(255,255,255,0.09);
            gap: 4px; display: inline-flex;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important; border-radius: 9px !important;
            font-weight: 500 !important; font-size: 13px !important;
            color: rgba(241,245,249,0.5) !important; border: none !important;
            padding: 7px 18px !important; transition: all 0.15s !important;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(59,130,246,0.18) !important;
            color: #93C5FD !important; font-weight: 600 !important;
            box-shadow: 0 0 16px rgba(59,130,246,0.2) !important;
        }

        /* ── Select / inputs ───────────────────────────────────────── */
        div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            border-color: rgba(255,255,255,0.12) !important;
            background: rgba(255,255,255,0.06) !important;
            color: #F1F5F9 !important;
        }
        div[data-baseweb="select"] > div:focus-within {
            border-color: rgba(59,130,246,0.5) !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.15), 0 0 20px rgba(59,130,246,0.1) !important;
        }
        input[type="text"], .stTextInput input {
            background: rgba(255,255,255,0.06) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 10px !important;
            color: #F1F5F9 !important;
        }
        input[type="text"]:focus, .stTextInput input:focus {
            border-color: rgba(59,130,246,0.5) !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
        }

        /* ── Dataframe ─────────────────────────────────────────────── */
        div[data-testid="stDataFrame"] > div {
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
            overflow: hidden;
            backdrop-filter: blur(16px) !important;
        }
        div.stAlert { border-radius: 12px !important; }

        /* ── Caption / small text ──────────────────────────────────── */
        .stCaption, [data-testid="stCaptionContainer"] p {
            color: rgba(241,245,249,0.45) !important;
        }

        /* ── Toggle ────────────────────────────────────────────────── */
        [data-testid="stToggle"] label {
            color: rgba(241,245,249,0.75) !important;
        }

        /* ── Footer ────────────────────────────────────────────────── */
        .app-footer {
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 14px 24px; margin-top: 28px;
            font-size: 12px; color: rgba(241,245,249,0.4);
        }
        .footer-left { display: flex; align-items: center; gap: 10px; }
        .footer-dot  {
            width: 3px; height: 3px; background: rgba(241,245,249,0.2); border-radius: 50%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()

# ══════════════════════════════════════════════════════════════════════════════
# UI COMPONENT BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def _e(text: str) -> str:
    return _html.escape(str(text))


def _safe_url(url: str) -> str:
    """Return url only if scheme is http/https; otherwise '#' to block javascript: XSS."""
    u = str(url).strip()
    return u if re.match(r"^https?://", u, re.I) else "#"


def render_app_header(api_ok: bool) -> None:
    api_badge = (
        '<span style="display:inline-flex;align-items:center;gap:6px;'
        'background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.25);'
        'border-radius:20px;padding:4px 12px;font-size:11px;font-weight:600;color:#34D399;">'
        '<span style="width:6px;height:6px;background:#34D399;border-radius:50%;'
        'box-shadow:0 0 6px rgba(52,211,153,0.8);display:inline-block;"></span>'
        'API Connected</span>'
        if api_ok else
        '<span style="display:inline-flex;align-items:center;gap:6px;'
        'background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.25);'
        'border-radius:20px;padding:4px 12px;font-size:11px;font-weight:600;color:#FCA5A5;">'
        '⚠ No API Key</span>'
    )
    st.markdown(
        f"""
        <div class="app-header">
          <div class="app-header-left">
            <div class="app-icon-wrap">📰</div>
            <div>
              <h1 class="app-title">Dasbor Pantauan Berita Ekonomi</h1>
              <p class="app-subtitle">BPS Kabupaten Lombok Tengah &nbsp;·&nbsp; Analisis PDRB 2026</p>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;position:relative;z-index:1;">
            {api_badge}
            <span class="live-badge">
              <span class="live-dot"></span>LIVE
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(df: pd.DataFrame, cfg: Dict) -> None:
    cards = [
        ("📄", "Total Berita",   str(len(df)),                             "#2563EB"),
        ("🏢", "Sumber Unik",   str(df["Sumber"].nunique()),               "#7C3AED"),
        ("📅", "Periode",        cfg.get("triwulan", "—").split(" ")[0],   "#059669"),
        ("📊", "Kategori KBLI",  cfg.get("kbli", "—"),                    "#D97706"),
    ]
    cols = st.columns(4)
    for col, (icon, label, value, color) in zip(cols, cards):
        col.markdown(
            f'<div class="kpi-card" style="--kpi-color:{color};">'
            f'<span class="kpi-icon">{icon}</span>'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{_e(value)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_progress_bar(step: int, total: int, msg: str) -> str:
    pct = int(min((step / max(total, 1)) * 100, 100))
    return (
        f'<div class="prog-wrap">'
        f'<div class="prog-header">'
        f'<span class="prog-msg">🔍 {_e(msg)}</span>'
        f'<span class="prog-pct">{pct}%</span>'
        f'</div>'
        f'<div class="prog-track"><div class="prog-fill" style="width:{pct}%;"></div></div>'
        f'</div>'
    )


def render_news_card(row: Dict) -> str:
    kat    = str(row.get("Kategori KBLI", "Lainnya"))
    color  = KBLI_COLORS.get(kat, "#6B7280")
    bg     = color + "18"   # ~10% opacity hex
    title   = _e(row.get("Judul Berita", ""))
    snippet = _e(row.get("Fenomena", ""))
    date_s  = _e(row.get("Tanggal", "—"))
    source  = _e(row.get("Sumber", ""))
    link    = _safe_url(row.get("Link", "#"))
    uraian  = _e(row.get("Uraian KBLI", ""))

    return (
        f'<div class="news-card">'
        f'<div class="news-meta">'
        f'<span class="kbli-tag" style="background:{bg};color:{color};">{_e(kat)}</span>'
        f'<span class="news-date">📅 {date_s}</span>'
        f'<span class="news-src">· {source}</span>'
        f'</div>'
        f'<p class="news-title">{title}</p>'
        f'<p class="news-snippet">{snippet}</p>'
        f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="news-link">Baca Selengkapnya →</a>'
        f'</div>'
    )


def render_empty_state(variant: str = "initial") -> None:
    if variant == "initial":
        icon, title, desc, cta = (
            "🗞️",
            "Belum Ada Data Berita",
            "Atur parameter pencarian di atas — pilih wilayah, triwulan, dan kategori lapangan usaha, lalu klik Mulai Pencarian.",
            "👆 Atur Filter & Mulai Pencarian",
        )
    else:
        icon, title, desc, cta = (
            "🔍",
            "Tidak Ada Hasil Ditemukan",
            "Tidak ada berita yang cocok untuk kombinasi filter ini. Coba ubah Triwulan, Wilayah, atau Kategori KBLI.",
            "↑ Ubah Parameter Pencarian",
        )
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-icon">{icon}</div>'
        f'<div class="empty-title">{title}</div>'
        f'<p class="empty-desc">{desc}</p>'
        f'<span class="empty-cta">{cta}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def donut_chart(df: pd.DataFrame) -> go.Figure:
    counts  = df["Sumber"].value_counts()
    palette = [
        "#3B82F6","#8B5CF6","#10B981","#F59E0B","#EF4444",
        "#06B6D4","#84CC16","#F97316","#6366F1","#14B8A6",
    ]
    fig = go.Figure(data=[go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.62,
        marker=dict(colors=palette[:len(counts)], line=dict(color="rgba(6,9,24,0.8)", width=3)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Inter, sans-serif", color="#F1F5F9"),
        hovertemplate="<b>%{label}</b><br>%{value} berita (%{percent})<extra></extra>",
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0), height=270,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F1F5F9"),
    )
    return fig


def render_sentiment_cards(df: pd.DataFrame) -> None:
    total     = max(len(df), 1)
    mendukung  = int((df["Dampak Ekonomi"] == "🟢 Mendukung").sum())
    netral     = int((df["Dampak Ekonomi"] == "🟡 Netral").sum())
    menghambat = int((df["Dampak Ekonomi"] == "🔴 Menghambat").sum())
    cards = [
        ("🟢", "Mendukung",  mendukung,  f"{mendukung /total*100:.0f}% berita", "rgba(16,185,129,0.10)", "rgba(52,211,153,0.7)", "#10B981"),
        ("🟡", "Netral",     netral,     f"{netral    /total*100:.0f}% berita", "rgba(245,158,11,0.10)", "rgba(251,191,36,0.7)", "#F59E0B"),
        ("🔴", "Menghambat", menghambat, f"{menghambat/total*100:.0f}% berita", "rgba(239,68,68,0.10)",  "rgba(252,165,165,0.8)", "#EF4444"),
    ]
    cols = st.columns(3)
    for col, (icon, label, value, sub, bg, text, accent) in zip(cols, cards):
        col.markdown(
            f'<div class="kpi-card" style="--kpi-color:{accent};background:{bg};border-color:{accent}40;">'
            f'<span class="kpi-icon">{icon}</span>'
            f'<div class="kpi-label" style="color:{text};">{label}</div>'
            f'<div class="kpi-value" style="color:#F1F5F9;">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def component_pie(df: pd.DataFrame) -> go.Figure:
    counts  = df["Komponen PDRB"].value_counts()
    labels: List[str] = []
    values: List[int] = []
    palette = ["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#94A3B8"]
    order   = list(PDRB_COMPONENTS.keys()) + ["Lainnya"]
    for comp in order:
        if comp in counts.index:
            cfg = PDRB_COMPONENTS.get(comp)
            labels.append(cfg["label"] if cfg else comp)
            values.append(int(counts[comp]))
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=palette[:len(labels)], line=dict(color="rgba(6,9,24,0.8)", width=3)),
        textinfo="label+percent",
        textfont=dict(size=11, family="Inter, sans-serif", color="#F1F5F9"),
        hovertemplate="<b>%{label}</b><br>%{value} berita (%{percent})<extra></extra>",
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0), height=270,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F1F5F9"),
    )
    return fig


def render_ringkasan(df: pd.DataFrame, cfg: Dict) -> None:
    total      = len(df)
    region     = cfg.get("region", "wilayah ini")
    triwulan   = cfg.get("triwulan", "triwulan ini").split(" (")[0]
    mendukung  = int((df["Dampak Ekonomi"] == "🟢 Mendukung").sum())
    menghambat = int((df["Dampak Ekonomi"] == "🔴 Menghambat").sum())
    _mode      = df["Komponen PDRB"].mode()
    top_komp   = _mode.iloc[0] if not _mode.empty else "—"
    comp_cfg   = PDRB_COMPONENTS.get(top_komp)
    top_label  = comp_cfg["label"] if comp_cfg else top_komp

    if mendukung > menghambat:
        tren = "didominasi sinyal positif yang berpotensi mendorong pertumbuhan PDRB"
    elif menghambat > mendukung:
        tren = "menunjukkan tekanan ekonomi yang perlu diwaspadai dalam proyeksi PDRB"
    else:
        tren = "menunjukkan kondisi ekonomi yang relatif berimbang"

    st.markdown(
        f'<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);'
        f'border-radius:14px;padding:18px 22px;margin-top:16px;'
        f'backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);">'
        f'<div style="font-size:10px;font-weight:700;color:rgba(147,197,253,0.8);'
        f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;">📋 Ringkasan Analis</div>'
        f'<p style="font-size:13.5px;color:rgba(241,245,249,0.82);line-height:1.75;margin:0;">'
        f'Berdasarkan <strong style="color:#F1F5F9;">{total} berita</strong>, tren ekonomi di '
        f'<strong style="color:#93C5FD;">{_e(region)}</strong> '
        f'pada <strong style="color:#93C5FD;">{_e(triwulan)}</strong> {tren}. '
        f'Komponen PDRB yang paling banyak teridentifikasi adalah <strong style="color:#F1F5F9;">{_e(top_label)}</strong>, '
        f'dengan <strong style="color:#6EE7B7;">{mendukung} berita mendukung</strong> dan '
        f'<strong style="color:#FCA5A5;">{menghambat} berita mengindikasikan hambatan</strong>.'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def trend_bar_chart(series: pd.Series, height: int = 260) -> go.Figure:
    fig = go.Figure(data=[go.Bar(
        x=series.index.tolist(),
        y=series.values.tolist(),
        marker=dict(
            color=series.values.tolist(),
            colorscale=[[0, "#1D4ED8"], [0.5, "#4F46E5"], [1, "#8B5CF6"]],
            line=dict(width=0),
        ),
        hovertemplate="%{x}<br>%{y} berita<extra></extra>",
    )])
    fig.update_layout(
        margin=dict(t=8, b=0, l=0, r=0), height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="rgba(241,245,249,0.65)"),
        xaxis=dict(showgrid=False, tickangle=-45, tickfont=dict(color="rgba(241,245,249,0.5)")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False,
                   tickfont=dict(color="rgba(241,245,249,0.5)")),
    )
    return fig


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Berita")
    return buf.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

# ── App Header ────────────────────────────────────────────────────────────────
render_app_header(bool(SERPER_API_KEY))

# ── Filtering Header ─────────────────────────────────────────────────────────
st.markdown('<div class="filter-wrap"><div class="section-eyebrow">🎯 Parameter Pencarian</div>', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns(3)
with fc1:
    region       = st.selectbox("🌏 Wilayah", REGIONS, index=0)
    triwulan_key = st.selectbox("📅 Triwulan", list(TRIWULAN_CONFIG.keys()), index=0)
with fc2:
    kbli_key     = st.selectbox("📊 Kategori KBLI", list(KBLI_MAPPING.keys()), index=0)
    num_results  = st.selectbox("📈 Hasil per Query", [5, 10, 15, 20], index=1)
with fc3:
    use_local    = st.toggle(
        "🌐 Aktifkan Portal Lokal NTB",
        value=True,
        help="Tambah data dari Suara NTB, Lombok Post, Radar Lombok, Koran Lombok",
    )
    kbli_cfg    = KBLI_MAPPING[kbli_key]
    tcfg        = TRIWULAN_CONFIG[triwulan_key]
    n_kw        = min(len(kbli_cfg["keywords"]), 5)
    est_calls   = n_kw * num_results
    st.caption(
        f"**{tcfg['start'].strftime('%d %b')} – {tcfg['end'].strftime('%d %b %Y')}**  \n"
        f"*{kbli_cfg['uraian']}*  \n"
        f"Estimasi ~**{est_calls} Serper API calls**"
    )
    scrape_btn = st.button("🔍 Mulai Pencarian", type="primary", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "df_result"      not in st.session_state: st.session_state.df_result      = pd.DataFrame()
if "last_config"    not in st.session_state: st.session_state.last_config    = {}
if "last_updated"   not in st.session_state: st.session_state.last_updated   = None
if "last_scrape_ts" not in st.session_state: st.session_state.last_scrape_ts = 0.0

_COOLDOWN_SEC = 30

if not st.session_state.df_result.empty:
    if st.button("🗑️ Hapus Hasil", help="Bersihkan hasil pencarian saat ini"):
        st.session_state.df_result    = pd.DataFrame()
        st.session_state.last_config  = {}
        st.session_state.last_updated = None
        st.rerun()

# ── Trigger Scrape ────────────────────────────────────────────────────────────
if scrape_btn:
    _elapsed = datetime.now().timestamp() - st.session_state.last_scrape_ts
    _remaining = int(_COOLDOWN_SEC - _elapsed)
    if _remaining > 0:
        st.warning(
            f"⏳ Tunggu **{_remaining} detik** sebelum pencarian berikutnya "
            f"untuk menjaga kuota Serper API."
        )
    elif not SERPER_API_KEY:
        st.error(
            "❌ `SERPER_API_KEY` tidak ditemukan.  \n"
            "Tambahkan di `.streamlit/secrets.toml` atau Streamlit Cloud → Settings → Secrets."
        )
    else:
        st.session_state.last_scrape_ts = datetime.now().timestamp()
        st.session_state.last_config = {
            "region":   region,
            "triwulan": triwulan_key,
            "kbli":     kbli_key,
            "ts":       datetime.now().strftime("%Y%m%d_%H%M"),
        }

        prog_ph = st.empty()

        def on_progress(step: int, total: int, msg: str) -> None:
            prog_ph.markdown(render_progress_bar(step, total, msg), unsafe_allow_html=True)

        df, err = run_scrape(
            api_key=SERPER_API_KEY,
            region=region,
            triwulan_key=triwulan_key,
            kbli_key=kbli_key,
            num_results=num_results,
            use_local=use_local,
            on_progress=on_progress,
        )

        prog_ph.empty()

        if err == "API_KEY_INVALID":
            st.error("❌ SERPER_API_KEY tidak valid — periksa Secrets.")
            df = pd.DataFrame()
        elif not df.empty:
            st.success(f"✅ Pencarian selesai — **{len(df)}** berita unik ditemukan.")
        else:
            st.warning("⚠️ Tidak ada berita ditemukan untuk parameter ini.")

        st.session_state.df_result    = df
        st.session_state.last_updated = datetime.now()

# ── Main Content ──────────────────────────────────────────────────────────────
df  = st.session_state.df_result
cfg = st.session_state.last_config

if not df.empty:

    # KPI Cards
    st.markdown("<div style='margin:4px 0 16px'></div>", unsafe_allow_html=True)
    render_kpi_cards(df, cfg)

    # Sentiment Cards
    has_analysis = "Dampak Ekonomi" in df.columns and df["Dampak Ekonomi"].notna().any()
    if has_analysis:
        st.markdown(
            '<p style="font-size:10px;font-weight:700;color:#9CA3AF;text-transform:uppercase;'
            'letter-spacing:0.12em;margin:18px 0 10px 2px;">📡 Analisis Dampak Ekonomi</p>',
            unsafe_allow_html=True,
        )
        render_sentiment_cards(df)
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # Tabs
    tab_tbl, tab_feed, tab_viz = st.tabs(["📋 Tabel Data", "📰 Umpan Berita", "📊 Analitik"])

    # ── Tab 1: Tabel Data ─────────────────────────────────────────────────────
    with tab_tbl:
        sf1, sf2, sf3 = st.columns([3, 2, 1])
        with sf1:
            srch = st.text_input(
                "", placeholder="🔎 Cari judul atau cuplikan berita...",
                label_visibility="collapsed",
            )
        with sf2:
            src_list   = ["Semua Sumber"] + sorted(df["Sumber"].dropna().unique().tolist())
            src_filter = st.selectbox("", src_list, label_visibility="collapsed")
        with sf3:
            tgl_only = st.checkbox("Ada tanggal", value=False)

        dv = df.copy()
        if srch:
            mask = (
                dv["Judul Berita"].str.contains(srch, case=False, na=False) |
                dv["Fenomena"].str.contains(srch, case=False, na=False)
            )
            dv = dv[mask]
        if src_filter != "Semua Sumber":
            dv = dv[dv["Sumber"] == src_filter]
        if tgl_only:
            dv = dv[dv["Tanggal"] != "—"]

        st.caption(f"Menampilkan **{len(dv)}** dari **{len(df)}** berita")
        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

        st.dataframe(
            dv,
            column_config={
                "Link":           st.column_config.LinkColumn("Tautan",          display_text="🔗 Buka"),
                "Judul Berita":   st.column_config.TextColumn("Judul Berita",    width="large"),
                "Uraian KBLI":    st.column_config.TextColumn("Uraian KBLI",     width="large"),
                "Fenomena":       st.column_config.TextColumn("Cuplikan Berita", width="large"),
                "Analisa Teori":  st.column_config.TextColumn("Analisa Teori",   width="large"),
                "Dampak Ekonomi": st.column_config.TextColumn("Dampak Ekonomi",  width="small"),
                "Komponen PDRB":  st.column_config.TextColumn("Komponen PDRB",   width="small"),
                "Tanggal":        st.column_config.TextColumn("Tanggal",         width="small"),
                "Sumber":         st.column_config.TextColumn("Sumber",          width="small"),
                "Kategori KBLI":  st.column_config.TextColumn("Kategori",        width="medium"),
            },
            use_container_width=True,
            height=480,
            hide_index=True,
        )

    # ── Tab 2: Umpan Berita ───────────────────────────────────────────────────
    with tab_feed:
        feed_col, _ = st.columns([2, 1])
        with feed_col:
            feed_search = st.text_input(
                "", placeholder="🔎 Saring judul berita...",
                label_visibility="collapsed", key="feed_search",
            )

        feed_df = df.copy()
        if feed_search:
            feed_df = feed_df[
                feed_df["Judul Berita"].str.contains(feed_search, case=False, na=False)
            ]

        st.caption(f"Menampilkan **{len(feed_df)}** artikel")
        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

        if feed_df.empty:
            render_empty_state("noresult")
        else:
            cards_html = "".join(
                render_news_card(row)
                for row in feed_df.head(50).to_dict(orient="records")
            )
            st.markdown(cards_html, unsafe_allow_html=True)
            if len(feed_df) > 50:
                st.caption(f"*Menampilkan 50 dari {len(feed_df)} artikel. Unduh Excel untuk data lengkap.*")

    # ── Tab 3: Analitik ──────────────────────────────────────────────────────
    with tab_viz:
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("**Distribusi Sumber Berita**")
            st.plotly_chart(donut_chart(df), use_container_width=True)
        with v2:
            if has_analysis and "Komponen PDRB" in df.columns:
                st.markdown("**Komponen PDRB Teridentifikasi**")
                st.plotly_chart(component_pie(df), use_container_width=True)
            else:
                st.markdown("**Tren Publikasi per Tanggal**")
                dated = df[df["Tanggal"] != "—"]["Tanggal"].value_counts().sort_index()
                if not dated.empty:
                    st.plotly_chart(trend_bar_chart(dated, height=260), use_container_width=True)
                else:
                    st.info("Tidak ada data tanggal yang bisa divisualisasikan.")

        if has_analysis:
            dated2 = df[df["Tanggal"] != "—"]["Tanggal"].value_counts().sort_index()
            if not dated2.empty:
                st.markdown("**Tren Publikasi per Tanggal**")
                st.plotly_chart(trend_bar_chart(dated2, height=220), use_container_width=True)

        uraian_val = df["Uraian KBLI"].iloc[0] if not df.empty else "—"
        st.markdown(
            f'<div style="background:rgba(59,130,246,0.08);border-left:3px solid #3B82F6;'
            f'border-radius:12px;padding:14px 18px;margin-top:10px;'
            f'backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">'
            f'<strong style="color:#93C5FD;font-size:13px;">{_e(cfg.get("kbli","—"))}</strong><br>'
            f'<span style="color:rgba(241,245,249,0.55);font-size:12.5px;">{_e(uraian_val)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    kbli_slug   = re.sub(r"[^a-zA-Z0-9]", "_", cfg.get("kbli", "KBLI"))
    region_slug = cfg.get("region", "Wilayah").replace(" ", "_")
    ts          = cfg.get("ts", datetime.now().strftime("%Y%m%d_%H%M"))
    filename    = f"berita_{kbli_slug}_{region_slug}_2026_{ts}"

    dl1, dl2, _ = st.columns([1, 1, 3])
    with dl1:
        st.download_button(
            "⬇️ Unduh Excel",
            data=to_excel_bytes(df),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇️ Unduh CSV",
            data=to_csv_bytes(df),
            file_name=f"{filename}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Ringkasan Analis & Disclaimer ─────────────────────────────────────────
    if has_analysis:
        render_ringkasan(df, cfg)
        st.markdown(
            '<p style="margin-top:12px;font-size:11.5px;color:rgba(241,245,249,0.35);'
            'font-style:italic;text-align:center;">'
            '⚠️ Analisis ini bersifat otomatis berbasis pencocokan kata kunci (rule-based AI). '
            'Hasil ini merupakan bahan pendukung awal dan perlu divalidasi oleh analis BPS '
            'sebelum digunakan sebagai dasar estimasi PDRB resmi.'
            '</p>',
            unsafe_allow_html=True,
        )

elif scrape_btn:
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    render_empty_state("noresult")

else:
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    render_empty_state("initial")

# ── App Footer ────────────────────────────────────────────────────────────────
last_updated = st.session_state.last_updated
ts_str = (
    f"Pembaruan terakhir: {last_updated.strftime('%d %b %Y, %H:%M WIB')}"
    if last_updated else "Belum ada data yang dimuat"
)
st.markdown(
    f'<div class="app-footer">'
    f'<div class="footer-left">'
    f'<span>📌 BPS Kabupaten Lombok Tengah</span>'
    f'<span class="footer-dot"></span>'
    f'<span>Data via Serper.dev + Portal NTB Lokal</span>'
    f'<span class="footer-dot"></span>'
    f'<span>Klasifikasi KBLI otomatis</span>'
    f'</div>'
    f'<span style="color:#9CA3AF;">🕐 {_e(ts_str)}</span>'
    f'</div>',
    unsafe_allow_html=True,
)
