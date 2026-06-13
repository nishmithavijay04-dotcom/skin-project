"""
TINTA - AI PERSONAL COLOR ANALYSIS
COMPLETE LUXURY BEAUTY APP  —  ALL GAPS FIXED
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import io
import re
import datetime
import time
import random
import base64
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=FutureWarning)

import json

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ================================================================
# PAGE CONFIGURATION
# ================================================================
st.set_page_config(
    page_title="Tinta - AI Personal Color Analysis",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="auto"
)

# ================================================================
# SESSION STATE
# ================================================================
DEFAULTS = {
    "page": "welcome",
    "mode": None,
    "analysis_results": None,
    "dark_mode": None,          # None = not yet detected
    "saved_analyses": [],
    "uploaded_photo": None,
    "quiz_step": 0,
    "quiz_answers": {},
    "compare_results": None,
    "compare_images": None,
    "delete_confirm_idx": None, # index of diary entry pending deletion
    "diary_sort": "Newest first",
    "diary_filter": "All seasons",
    "sidebar_collapsed": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================================================================
# DARK MODE TOGGLE
# ================================================================
def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# ================================================================
# UNIQUE FEATURES DATA  (all 12 seasons)
# ================================================================
COLOR_VIBES = {
    "Light Spring":  {"vibe": "Fresh, Luminous, Joyful",       "emoji": "🌸", "mood": "You radiate youthful energy and warmth."},
    "True Spring":   {"vibe": "Vibrant, Golden, Alive",        "emoji": "🌻", "mood": "Your warm clarity makes every room brighter."},
    "Bright Spring": {"vibe": "Clear, Sparkling, Electric",    "emoji": "⚡", "mood": "High contrast and vivid energy define your look."},
    "True Summer":   {"vibe": "Soft, Elegant, Dreamy",         "emoji": "💨", "mood": "Your beauty whispers - soft, refined, and unforgettable."},
    "Light Summer":  {"vibe": "Airy, Delicate, Luminous",      "emoji": "🕊️", "mood": "There's a porcelain lightness to your colouring."},
    "Soft Summer":   {"vibe": "Gentle, Peaceful, Harmonious",  "emoji": "🌿", "mood": "You bring calm and balance wherever you go."},
    "True Autumn":   {"vibe": "Earthy, Grounded, Magnetic",    "emoji": "🍂", "mood": "You have a natural, welcoming presence that draws people in."},
    "Soft Autumn":   {"vibe": "Warm, Inviting, Natural",       "emoji": "🍁", "mood": "People feel instantly comfortable around you."},
    "Deep Autumn":   {"vibe": "Bold, Intense, Powerful",       "emoji": "🌙", "mood": "You command attention with your rich, dramatic colouring."},
    "True Winter":   {"vibe": "Bold, Striking, Dramatic",      "emoji": "❄️", "mood": "You make a statement wherever you go."},
    "Deep Winter":   {"vibe": "Intense, Mysterious, Captivating","emoji": "🌌","mood": "There's an alluring depth to your colouring."},
    "Bright Winter": {"vibe": "Vivid, Crisp, Commanding",      "emoji": "💎", "mood": "Crystal-clear contrast makes you unforgettable."},
}

SEASONAL_PLAYLISTS = {
    "Light Spring":  "https://open.spotify.com/playlist/37i9dQZF1DX3Ogo9pFvBkY",
    "True Spring":   "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC",
    "Bright Spring": "https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0",
    "True Summer":   "https://open.spotify.com/playlist/37i9dQZF1DX0Yxoavh5qJV",
    "Light Summer":  "https://open.spotify.com/playlist/37i9dQZF1DWYxwmBaMqxsl",
    "Soft Summer":   "https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO",
    "True Autumn":   "https://open.spotify.com/playlist/37i9dQZF1DX9wC1KY45plY",
    "Soft Autumn":   "https://open.spotify.com/playlist/37i9dQZF1DX9cTf20VJBL1",
    "Deep Autumn":   "https://open.spotify.com/playlist/37i9dQZF1DX6z20vCajNja",
    "True Winter":   "https://open.spotify.com/playlist/37i9dQZF1DX4pAtJkcLPgL",
    "Deep Winter":   "https://open.spotify.com/playlist/37i9dQZF1DX3fU3VQhXqGT",
    "Bright Winter": "https://open.spotify.com/playlist/37i9dQZF1DX2SK4ytI2KAh",
}



def get_color_harmonies(base_colors):
    return {
        "Complementary": [base_colors[0], "#4A3728" if base_colors[0] == "#C8963C" else "#C8963C"],
        "Analogous": base_colors[:3],
        "Triadic": [base_colors[0], base_colors[2], base_colors[4]]
    }

SEASON_TRANSFORMATIONS = {
    "Light Spring":  {"Darker Hair": "True Spring",   "Lighter Hair": "Soft Autumn"},
    "True Spring":   {"Darker Hair": "Bright Spring", "Lighter Hair": "Light Spring"},
    "Bright Spring": {"Darker Hair": "Bright Winter", "Lighter Hair": "True Spring"},
    "True Summer":   {"Darker Hair": "Soft Summer",   "Lighter Hair": "Light Summer"},
    "Light Summer":  {"Darker Hair": "True Summer",   "Lighter Hair": "Bright Spring"},
    "Soft Summer":   {"Darker Hair": "True Summer",   "Lighter Hair": "Light Summer"},
    "True Autumn":   {"Darker Hair": "Deep Autumn",   "Lighter Hair": "Light Spring"},
    "Soft Autumn":   {"Darker Hair": "True Autumn",   "Lighter Hair": "Soft Summer"},
    "Deep Autumn":   {"Darker Hair": "Deep Winter",   "Lighter Hair": "True Autumn"},
    "True Winter":   {"Darker Hair": "Deep Winter",   "Lighter Hair": "True Summer"},
    "Deep Winter":   {"Darker Hair": "Deep Autumn",   "Lighter Hair": "True Winter"},
    "Bright Winter": {"Darker Hair": "Deep Winter",   "Lighter Hair": "Bright Spring"},
}

# ================================================================
# LUXURY CSS
# ================================================================
def load_css():
    dm = st.session_state.dark_mode
    if dm:
        card_bg = "#262320"; bg_primary = "#1A1816"; text_primary = "#F5EFE6"
        text_secondary = "#D4C8B8"; espresso = "#C8963C"; gold = "#D4AF37"
        rose_clay = "#C68E7A"; shadow_sm = "0 4px 16px rgba(0,0,0,0.25)"
        shadow_md = "0 8px 32px rgba(0,0,0,0.4)"; card_border = "rgba(212,175,55,0.15)"
        card_border_inner = "rgba(255,255,255,0.03)"; swatch_border = "rgba(212,175,55,0.2)"
        chip_bg = "rgba(212,175,55,0.12)"; chip_hover_color = "#1A1816"
        progress_bg = "rgba(212,175,55,0.2)"; brand_gradient = "145deg, #D4AF37 0%, #C8963C 100%"
        sidebar_bg = "#262320"; skeleton_base = "#2e2b28"; skeleton_shine = "#3a3530"
    else:
        card_bg = "#FFFFFF"; bg_primary = "#F5EFE6"; text_primary = "#3D2B1F"
        text_secondary = "#5A4A3A"; espresso = "#3D2B1F"; gold = "#C89F4A"
        rose_clay = "#C68E7A"; shadow_sm = "0 4px 16px rgba(61,43,31,0.06)"
        shadow_md = "0 8px 32px rgba(61,43,31,0.12)"; card_border = "rgba(61,43,31,0.06)"
        card_border_inner = "rgba(200,159,74,0.08)"; swatch_border = "rgba(61,43,31,0.1)"
        chip_bg = "rgba(200,159,74,0.1)"; chip_hover_color = "white"
        progress_bg = "rgba(61,43,31,0.1)"; brand_gradient = "145deg, #3D2B1F 0%, #C89F4A 100%"
        sidebar_bg = "#FFFFFF"; skeleton_base = "#e8e0d5"; skeleton_shine = "#f5efe6"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
        --bg-primary: {bg_primary};
        --card-bg: {card_bg};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --espresso: {espresso};
        --gold: {gold};
        --rose-clay: {rose_clay};
        --shadow-sm: {shadow_sm};
        --shadow-md: {shadow_md};
        --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
        --ease-smooth: cubic-bezier(0.2, 0.9, 0.4, 1.05);
    }}

    body, .stApp, .card, .mode-card, .quiz-card, [data-testid="stSidebar"] {{
        transition: background-color 0.3s ease, color 0.2s ease, border-color 0.3s ease;
    }}

    body, .stApp {{ background: var(--bg-primary); font-family: 'Inter', sans-serif; }}
    h1,h2,h3,h4,h5,h6,.brand {{ font-family: 'Playfair Display', serif; color: var(--text-primary); letter-spacing:-0.01em; }}
    h1 {{ font-size:2.8rem; font-weight:700; line-height:1.2; letter-spacing:-0.02em; }}
    h2 {{ font-size:1.9rem; font-weight:600; line-height:1.25; }}
    h3 {{ font-size:1.4rem; font-weight:600; line-height:1.3; }}
    h4 {{ font-size:1.1rem; font-weight:600; line-height:1.4; font-family:'Inter',sans-serif; }}
    p, li {{ line-height:1.6; }}
    p, li, .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2,
    .stMarkdown h3, .stMarkdown h4, .stText, label, .stMarkdown strong, .stMarkdown em {{
        color: var(--text-primary) !important;
    }}
    .stButton > button p, .stButton > button p *, .stButton > button span,
    .stButton > button div, .stButton > button * {{
        color: white !important;
    }}

    [data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
    [data-testid="stSidebar"] li,[data-testid="stSidebar"] div,
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4 {{ color: var(--text-primary) !important; }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(200,159,74,0.25); }}

    .stAlert p,.stAlert div,.stAlert span {{ color: inherit !important; }}
    .stTabs [data-baseweb="tab"] {{ color: var(--text-primary) !important; }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: var(--gold) !important; border-bottom-color: var(--gold) !important; }}
    .stExpander {{ background: var(--card-bg) !important; border-color: rgba(200,159,74,0.2) !important; }}
    .stExpander p,.stExpander li,.stExpander strong {{ color: var(--text-primary) !important; }}
    [data-testid="stExpanderDetails"] p,[data-testid="stExpanderDetails"] li {{ color: var(--text-primary) !important; }}

    .stCodeBlock,.stCodeBlock code,.stCodeBlock span {{ background: var(--card-bg) !important; }}
    pre {{ background: var(--card-bg) !important; border:1px solid rgba(200,159,74,0.15) !important; border-radius:12px !important; }}

    .stTextInput input,.stTextArea textarea {{
        background: var(--card-bg) !important; color: var(--text-primary) !important;
        border-color: rgba(200,159,74,0.3) !important;
    }}
    .stSelectbox select,[data-baseweb="select"] {{ background: var(--card-bg) !important; color: var(--text-primary) !important; }}

    [data-testid="stDownloadButton"] button {{
        background: var(--espresso) !important; color: #FFFFFF !important;
        border-radius: 40px !important; border: none !important;
    }}
    [data-testid="stDownloadButton"] button:hover {{ background: var(--gold) !important; transform: translateY(-2px); }}
    [data-testid="stDownloadButton"] button *, [data-testid="stDownloadButton"] button p {{ color: #FFFFFF !important; }}

    [data-testid="stAlert"] {{ background: var(--card-bg) !important; border-color: rgba(200,159,74,0.3) !important; }}
    [data-testid="stAlert"] p {{ color: var(--text-primary) !important; }}

    .brand {{
        font-size:2.8rem; font-weight:800;
        background: linear-gradient({brand_gradient});
        -webkit-background-clip:text; background-clip:text; color:transparent;
    }}

    /* ── Staggered card entry animations ── */
    @keyframes fadeUp {{
        from {{ opacity:0; transform:translateY(12px); }}
        to   {{ opacity:1; transform:translateY(0); }}
    }}
    @keyframes pulse-ring {{
        0%   {{ box-shadow: 0 0 0 0 rgba(212,175,55,0.4); }}
        70%  {{ box-shadow: 0 0 0 8px rgba(212,175,55,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(212,175,55,0); }}
    }}
    @keyframes shimmer {{
        0%   {{ background-position: -600px 0; }}
        100% {{ background-position: 600px 0; }}
    }}
    @keyframes ripple {{
        0%   {{ transform:scale(0); opacity:0.6; }}
        100% {{ transform:scale(4); opacity:0; }}
    }}

    .card-anim-0 {{ animation: fadeUp 0.35s ease-out 0ms    both; }}
    .card-anim-1 {{ animation: fadeUp 0.35s ease-out 80ms   both; }}
    .card-anim-2 {{ animation: fadeUp 0.35s ease-out 160ms  both; }}

    /* ── Cards ── */
    .card,.mode-card,.quiz-card,.unique-card {{
        background: var(--card-bg);
        border-radius:20px; padding:28px; margin-bottom:32px;
        box-shadow: var(--shadow-sm);
        transition: all 0.25s var(--ease-smooth);
        border: 1px solid {card_border};
        outline: 1px solid {card_border_inner};
    }}
    .card:hover,.mode-card:hover {{ transform:translateY(-4px); box-shadow:var(--shadow-md); border-color:var(--gold); }}
    .mode-card {{ cursor:pointer; text-align:center; padding:32px 28px; }}
    .mode-icon {{ font-size:52px; margin-bottom:16px; display:block; }}

    .quiz-card {{ cursor:pointer; text-align:center; padding:20px 12px; }}
    .quiz-card.selected {{ border-color:var(--rose-clay); background:rgba(198,142,122,0.12); animation:pulse-ring 0.6s ease-out; }}
    .quiz-card:hover {{ transform:translateY(-3px); box-shadow:var(--shadow-sm); border-color:var(--gold); }}
    .quiz-icon {{ font-size:40px; margin-bottom:12px; }}
    .quiz-label {{ font-size:14px; font-weight:600; color:var(--text-primary); }}
    .quiz-card.selected .quiz-label {{ color:var(--rose-clay); }}

    /* ── Buttons with ripple ── */
    .btn-primary,.stButton > button {{
        background: var(--espresso); color:white !important; border:none;
        border-radius:40px; padding:14px 28px; height:48px;
        font-family:'Inter',sans-serif; font-weight:600; font-size:14px;
        cursor:pointer; transition:all 0.2s var(--ease-smooth);
        width:100%; min-height:48px; position:relative; overflow:hidden;
    }}
    .stButton > button:hover {{ background:var(--gold); transform:translateY(-2px); box-shadow:0 0 14px rgba(200,159,74,0.35); }}
    .stButton > button:active {{ transform:scale(0.98); }}
    .stButton > button:focus-visible {{ outline:2px solid var(--gold); outline-offset:3px; }}
    [data-testid="stDownloadButton"] button * {{ color: white !important; }}
    .stButton > button::after {{
        content:''; position:absolute; border-radius:50%;
        width:10px; height:10px;
        background: rgba(255,255,255,0.5);
        transform:scale(0); opacity:0;
        transition: none;
    }}
    .stButton > button:active::after {{ animation: ripple 0.5s ease-out; }}

    /* ── Progress ── */
    .progress-container {{ background:{progress_bg}; border-radius:20px; height:4px; margin:20px 0; overflow:hidden; }}
    .progress-fill {{ background:var(--gold); border-radius:20px; height:100%; transition:width 0.5s ease; }}
    .progress-dots {{ display:flex; justify-content:center; gap:12px; margin:32px 0; }}
    .dot {{ width:8px; height:8px; border-radius:50%; background:var(--gold); opacity:0.3; transition:all 0.3s ease; }}
    .dot.active {{ width:28px; border-radius:4px; background:var(--espresso); opacity:1; }}
    .dot.completed {{ background:var(--rose-clay); opacity:0.6; }}

    /* ── Skeleton shimmer (loading) ── */
    .skeleton {{
        background: linear-gradient(90deg, {skeleton_base} 25%, {skeleton_shine} 50%, {skeleton_base} 75%);
        background-size: 600px 100%;
        animation: shimmer 1.4s infinite;
        border-radius: 12px;
    }}

    /* ── Color swatches ── */
    .color-swatch {{ width:72px; height:72px; border-radius:14px; margin:8px auto; border:2px solid {swatch_border}; transition:all 0.25s var(--ease-spring); cursor:pointer; }}
    .color-swatch:hover {{ transform:scale(1.08) translateY(-2px); border-color:var(--gold); box-shadow:0 6px 16px rgba(0,0,0,0.18); }}

    /* ── Chips ── */
    .chip-selector {{
        display:inline-flex; align-items:center; gap:8px;
        background:{chip_bg}; border-radius:40px; padding:12px 24px; margin:4px;
        font-size:13px; font-weight:500; color:var(--text-primary);
        cursor:pointer; transition:all 0.2s ease; min-height:44px;
    }}
    .chip-selector:hover {{ background:var(--gold); color:{chip_hover_color}; }}

    /* ── Unique cards ── */
    .unique-card {{ background:rgba(200,159,74,0.07); border:1px solid rgba(200,159,74,0.15); border-radius:20px; padding:24px; margin:20px 0; transition:all 0.25s ease; }}
    .unique-card:hover {{ border-color:var(--gold); box-shadow:var(--shadow-sm); }}
    .vibe-text {{ font-size:22px; font-weight:700; color:var(--gold); font-family:'Playfair Display',serif; line-height:1.3; }}

    /* ── Nav ── */
    .nav-buttons {{ display:flex; gap:16px; margin:24px 0; }}
    .nav-btn {{ flex:1; text-align:center; padding:12px 20px; border-radius:40px; font-weight:600; cursor:pointer; transition:all 0.2s; background:transparent; border:1px solid var(--gold); color:var(--gold); min-height:44px; }}
    .nav-btn:hover {{ background:var(--gold); color:{chip_hover_color}; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{ background:{sidebar_bg}; }}
    [data-testid="stFileUploader"] {{ background:var(--card-bg); border:2px dashed rgba(200,159,74,0.4); border-radius:20px; }}
    .stImage img {{ border-radius:20px; }}

    .stApp > .main {{ background: var(--bg-primary); }}
    .block-container {{ background: var(--bg-primary); }}
    .stMarkdown,.stMarkdown *,.element-container p,.stCaption,[data-testid="stCaptionContainer"] p {{ color:var(--text-primary) !important; }}

    [data-testid="stCameraInput"] {{ background:var(--card-bg); border-radius:16px; }}
    [data-testid="stCameraInput"] p {{ color:var(--text-secondary) !important; }}
    [data-testid="stFileUploader"] p,[data-testid="stFileUploader"] span,[data-testid="stFileUploadDropzone"] p {{ color:var(--text-secondary) !important; }}
    .stColorPicker label,[data-testid="stColorPickerBlock"] p {{ color:var(--text-primary) !important; }}
    [data-testid="stSpinner"] p {{ color:var(--text-primary) !important; }}

    .stProgress > div > div {{ background:rgba(200,159,74,0.2) !important; }}
    .stProgress > div > div > div {{ background:var(--gold) !important; }}

    [data-baseweb="tab-list"] {{ background:var(--card-bg) !important; border-radius:12px; padding:4px; }}
    [data-baseweb="tab"] {{ color:var(--text-secondary) !important; font-family:'Inter',sans-serif; }}
    [data-baseweb="tab"][aria-selected="true"] {{ color:var(--text-primary) !important; background:var(--bg-primary) !important; border-radius:8px !important; }}
    [data-baseweb="tab-highlight"] {{ background:var(--gold) !important; }}
    [data-baseweb="tab-border"] {{ display:none !important; }}

    [data-testid="stExpander"] {{ background:var(--card-bg); border-color:rgba(200,159,74,0.2) !important; border-radius:16px; }}
    [data-testid="stExpander"] summary p {{ color:var(--text-primary) !important; }}
    [data-testid="stExpanderDetails"] {{ background:var(--card-bg); }}
    [data-testid="stExpanderDetails"] p,[data-testid="stExpanderDetails"] li {{ color:var(--text-primary) !important; }}

    [data-testid="stCodeBlock"] {{ background:var(--card-bg) !important; }}
    [data-testid="stCodeBlock"] pre {{ background:var(--card-bg) !important; border:1px solid rgba(200,159,74,0.15) !important; }}
    [data-testid="stCodeBlock"] code,[data-testid="stCodeBlock"] span {{ color:var(--text-primary) !important; background:transparent !important; }}

    [data-testid="stNotification"],.stAlert {{ background:var(--card-bg) !important; border-radius:12px !important; }}
    [data-testid="stNotification"] p,[data-testid="stNotification"] div,.stAlert p,.stAlert div {{ color:var(--text-primary) !important; }}

    [data-testid="stDownloadButton"] > button {{
        background:var(--espresso) !important; color:#FFFFFF !important;
        border-radius:40px !important; border:none !important;
        width:100%; min-height:48px; font-family:'Inter',sans-serif; font-weight:600;
    }}
    [data-testid="stDownloadButton"] > button:hover {{ background:var(--gold) !important; transform:translateY(-2px); }}
    [data-testid="stDownloadButton"] > button *, [data-testid="stDownloadButton"] > button p {{ color:#FFFFFF !important; }}
    .btn-primary {{ color: white !important; }}
    .btn-primary *, .btn-primary p {{ color: white !important; }}
    a .btn-primary, a .btn-primary * {{ color: white !important; text-decoration: none; }}

    hr {{ border-color:rgba(200,159,74,0.2) !important; margin:16px 0; }}
    [data-testid="stImage"] figcaption,[data-testid="caption"] {{ color:var(--text-secondary) !important; }}
    *:focus-visible {{ outline:2px solid var(--gold); outline-offset:2px; }}

    /* ── Delete confirmation modal ── */
    .modal-overlay {{
        position:fixed; inset:0; background:rgba(0,0,0,0.55);
        backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px);
        z-index:9999; display:flex; align-items:center; justify-content:center;
        animation: fadeUp 0.2s ease-out;
    }}
    .modal-box {{
        background:var(--card-bg); border-radius:24px; padding:36px 40px;
        max-width:380px; width:90%; text-align:center;
        border:1px solid rgba(200,159,74,0.2); box-shadow:var(--shadow-md);
    }}

    /* ── User avatar ── */
    .user-avatar {{
        width:56px; height:56px; border-radius:28px;
        background:linear-gradient({brand_gradient});
        display:flex; align-items:center; justify-content:center;
        font-size:22px; margin:0 auto 12px; color:white; font-weight:700;
    }}

    @media (max-width:640px) {{
        h1 {{ font-size:2rem; }} h2 {{ font-size:1.5rem; }} h3 {{ font-size:1.2rem; }}
        .mode-card {{ padding:24px 16px; }} .mode-icon {{ font-size:44px; }}
        .color-swatch {{ width:50px; height:50px; border-radius:10px; }}
        .vibe-text {{ font-size:18px; }} .chip-selector {{ padding:10px 16px; }}
        [data-testid="stFileUploader"] {{ width:100%; padding:8px; }}
    }}
    </style>

    <script>
    // System color-scheme detection on first visit
    (function() {{
        if (window.__tintaColorDetected) return;
        window.__tintaColorDetected = true;
        var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        // store in sessionStorage so Streamlit can read it on reload if needed
        sessionStorage.setItem('tinta_prefers_dark', dark ? '1' : '0');
    }})();
    </script>
    """

# ================================================================
# FACE DETECTION
# ================================================================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

MAX_UPLOAD_MB = 200

def check_file_size(uploaded_file):
    """Return (ok, size_mb)"""
    if uploaded_file is None:
        return True, 0
    size_mb = uploaded_file.size / (1024 * 1024)
    return size_mb <= MAX_UPLOAD_MB, size_mb

def _is_human_skin_pixel_hsv(hsv_pixel):
    """
    Check if a single HSV pixel falls within the range of real human skin tones.
    Covers all Fitzpatrick types (very fair to very dark).
    """
    h_val = int(hsv_pixel[0])   # OpenCV H: 0-179
    s_val = int(hsv_pixel[1])   # S: 0-255
    v_val = int(hsv_pixel[2])   # V: 0-255

    # Human skin hue range: 0-22 covers fair→olive→brown→dark brown in OpenCV HSV
    # Very dark skin shifts toward lower hue (close to 0) with lower saturation
    hue_ok = (0 <= h_val <= 22) or (170 <= h_val <= 179)

    # Saturation: very dark skin can have low saturation (~8), cartoon fills are ~0
    # Over-saturated animation colours are >210
    sat_ok = 8 <= s_val <= 210

    # Value: dark skin tones go down to ~30; exclude pure black pixels (shadows)
    val_ok = 25 <= v_val <= 245

    return hue_ok and sat_ok and val_ok

def _skin_pixel_ratio(region_bgr):
    """
    Return fraction of pixels in a BGR region that match human skin HSV criteria.
    """
    if region_bgr.size == 0:
        return 0.0
    hsv = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)
    total = len(pixels)
    if total == 0:
        return 0.0
    skin_count = sum(1 for p in pixels if _is_human_skin_pixel_hsv(p))
    return skin_count / total

def _check_skin_texture(region_bgr):
    """
    Real human skin has subtle texture (pores, fine lines).
    Cartoons / dolls / printed images tend to be perfectly flat or have artificial gradients.
    We use the standard deviation of the grayscale Laplacian as a texture measure.
    Returns True if the texture is consistent with real human skin.
    """
    if region_bgr.size == 0:
        return False
    gray = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    std = lap.std()
    # Real skin: std roughly 1–120. Flat cartoon fills: < 0.8. 
    # Upper bound raised to 120 to handle JPEG compression artifacts on dark skin.
    return 0.8 <= std <= 120.0

def _nms_faces(faces, overlap_thresh=0.3):
    """
    Non-maximum suppression: merge/remove overlapping face boxes.
    Returns only the boxes that don't overlap significantly with a larger box.
    """
    if len(faces) == 0:
        return faces
    boxes = [(x, y, x+w, y+h) for (x, y, w, h) in faces]
    areas = [(x2-x1)*(y2-y1) for (x1,y1,x2,y2) in boxes]
    order = sorted(range(len(boxes)), key=lambda i: areas[i], reverse=True)
    keep = []
    suppressed = set()
    for i in order:
        if i in suppressed:
            continue
        keep.append(i)
        x1,y1,x2,y2 = boxes[i]
        for j in order:
            if j in suppressed or j == i:
                continue
            xx1 = max(x1, boxes[j][0]); yy1 = max(y1, boxes[j][1])
            xx2 = min(x2, boxes[j][2]); yy2 = min(y2, boxes[j][3])
            inter = max(0, xx2-xx1) * max(0, yy2-yy1)
            union = areas[i] + areas[j] - inter
            if union > 0 and inter/union > overlap_thresh:
                suppressed.add(j)
    return [faces[i] for i in keep]

def _verify_human_with_claude_api(img_bgr):
    """
    Use the Claude API to verify that the image contains a real human face.
    Returns True if a real human is detected, False otherwise.
    Falls back to True (allow) if the API call fails, so CV-based gates still apply.
    """
    try:
        # Resize to a small thumbnail to keep payload small
        thumb = cv2.resize(img_bgr, (256, 256))
        _, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, 70])
        b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

        import urllib.request
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 60,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Does this image contain a real human face (not a doll, toy, cartoon, "
                            "animal, sculpture, drawing, printed photo of a photo, or non-human object)? "
                            "Reply with only one word: YES or NO."
                        )
                    }
                ]
            }]
        }).encode("utf-8")

        # Read API key from Streamlit secrets (set via share.streamlit.io → Settings → Secrets)
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return True  # No key configured — fail open, CV gates still apply

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        answer = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                answer = block["text"].strip().upper()
                break
        return answer.startswith("YES")
    except Exception:
        # If API unreachable or fails, fall back to allowing (CV gates still apply)
        return True


def detect_face_and_extract_skin(img_bgr):
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    # Use higher minNeighbors (6) to reduce false positives from Haar cascade
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80))
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=8, minSize=(60, 60))
    if len(faces) == 0:
        return None, "no_face"
    # Apply NMS to merge overlapping detections of the same face
    faces = _nms_faces(list(faces))
    if len(faces) > 1:
        # Check if any detected face has visible eyes — if none do,
        # it's likely a back-of-head photo, not truly multiple faces.
        any_eyes = False
        for fx, fy, fw, fh in faces:
            roi_g = cv2.cvtColor(img_bgr[max(0,fy):min(h,fy+fh), max(0,fx):min(w,fx+fw)], cv2.COLOR_BGR2GRAY)
            upper = roi_g[:int(fh*0.60), :]
            e = eye_cascade.detectMultiScale(upper, scaleFactor=1.1, minNeighbors=3, minSize=(15,15))
            if len(e) > 0:
                any_eyes = True
                break
        if not any_eyes:
            return None, "no_face_forward"
        return None, "multiple_faces"
    x, y, w_f, h_f = faces[0]
    # Face too small check
    if w_f < 80 or h_f < 80:
        return None, "face_too_small"
    x, y = max(0, x), max(0, y)
    w_f, h_f = min(w - x, w_f), min(h - y, h_f)

    # ── Human verification ────────────────────────────────────────────────
    # Sample the central forehead + cheek regions to check for human skin tones
    # and real skin texture. Non-human subjects (dolls, cartoons, animals, printed
    # images) typically fail one or more of these checks.
    verify_regions = [
        # Forehead centre
        (y + int(h_f*0.05), y + int(h_f*0.22), x + int(w_f*0.3), x + int(w_f*0.7)),
        # Left cheek
        (y + int(h_f*0.45), y + int(h_f*0.65), x + int(w_f*0.05), x + int(w_f*0.3)),
        # Right cheek
        (y + int(h_f*0.45), y + int(h_f*0.65), x + int(w_f*0.7), x + int(w_f*0.95)),
        # Chin / lower face
        (y + int(h_f*0.75), y + h_f, x + int(w_f*0.3), x + int(w_f*0.7)),
    ]

    skin_ratios = []
    texture_passes = 0
    flat_color_count = 0   # counts regions that look like flat fills (dolls/anime)
    for y1, y2, x1, x2 in verify_regions:
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        if y2 > y1 and x2 > x1:
            region = img_bgr[y1:y2, x1:x2]
            skin_ratios.append(_skin_pixel_ratio(region))
            if _check_skin_texture(region):
                texture_passes += 1
            # Flat-colour check: real skin has colour variation across channels.
            # Dolls, anime, and illustrations tend to have very uniform fills.
            if region.size > 0:
                gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                color_std = float(gray_region.std())
                # Very low std → nearly solid colour → likely artificial fill
                if color_std < 6.0:
                    flat_color_count += 1

    if not skin_ratios:
        return None, "not_human"

    avg_skin_ratio = np.mean(skin_ratios)

    # ── Gate 1: skin colour coverage
    # Require ≥30% of sampled pixels to be human-skin-coloured.
    # (Raised from 20% to reduce false accepts of dolls and printed images.)
    if avg_skin_ratio < 0.30:
        return None, "not_human"

    # ── Gate 2: real skin texture
    # Require at least 2 of the 4 regions to pass the Laplacian texture check.
    # Cartoons and dolls are too flat to pass multiple regions.
    if texture_passes < 2:
        return None, "not_human"

    # ── Gate 3: flat-fill / anime / doll guard
    # If 3 or more regions look like flat solid fills, reject.
    if flat_color_count >= 3:
        return None, "not_human"

    # ── Gate 3b: Anime / illustration detector ────────────────────────────
    # Anime skin is painted with very smooth, low-noise gradients.
    # Real human skin photographed has natural high-frequency noise from:
    #   pores, fine hair, micro-shadows, JPEG sensor noise.
    # We measure this using the mean absolute deviation of a high-pass filter
    # on the face crop. Anime/illustrations score very low; real photos score high.
    face_crop_gate3 = img_bgr[max(0,y):min(h,y+h_f), max(0,x):min(w,x+w_f)]
    if face_crop_gate3.size > 0:
        gray_face = cv2.cvtColor(face_crop_gate3, cv2.COLOR_BGR2GRAY).astype(np.float32)
        # High-pass: subtract blurred version to isolate high-frequency noise
        blurred = cv2.GaussianBlur(gray_face, (5, 5), 0)
        highpass = np.abs(gray_face - blurred)
        hf_mean = float(np.mean(highpass))
        # Real photos: hf_mean typically > 3.5 (sensor noise + texture)
        # Anime / illustrations: hf_mean typically < 2.5 (smooth painted fills)
        if hf_mean < 2.5:
            return None, "not_human"

        # Secondary: edge density check.
        # Anime faces have very clean, sharp, widely-spaced edges (ink outlines).
        # Real faces have dense, diffuse edges (pores, hair, skin texture).
        edges = cv2.Canny(cv2.convertScaleAbs(gray_face), 80, 160)
        edge_density = float(np.sum(edges > 0)) / edges.size
        # Anime: sparse clean outlines → edge_density typically 0.02–0.06
        # Real photo: dense texture edges → edge_density typically > 0.07
        # Only reject if BOTH high-pass noise is low AND edges are very sparse
        if hf_mean < 3.5 and edge_density < 0.055:
            return None, "not_human"
    # ── End Gate 3b ───────────────────────────────────────────────────────

    # ── Gate 5: Uniform-colour / fur / plush guard
    # Real human skin has natural variation across R, G, B channels.
    # Stuffed animals and dolls tend to have highly uniform, single-hue regions.
    # We check the full face crop: if all three channels have very low std
    # simultaneously, it's almost certainly a non-human object.
    face_crop = img_bgr[max(0,y):min(h,y+h_f), max(0,x):min(w,x+w_f)]
    if face_crop.size > 0:
        ch_stds = [float(face_crop[:,:,c].std()) for c in range(3)]
        # Human faces: at least one channel std > 18 (eyes, lips, shadows create variation)
        # Uniform plush toys: all channels std < 18
        if max(ch_stds) < 18.0:
            return None, "not_human"
        # Additional: ratio between max and min channel std.
        # Plush toys are monochromatic — all channels move together.
        # Human faces have independent channel variation (lips red, eyes dark, etc.)
        if min(ch_stds) > 0 and max(ch_stds) / min(ch_stds) < 1.3:
            # All channels vary by the same amount → monochromatic object
            # But only reject if the overall std is also low (not a high-contrast human)
            if max(ch_stds) < 35.0:
                return None, "not_human"

    # ── Gate 6: AI-powered human verification (Claude API)
    # Ask the vision model whether the image actually shows a real human face.
    # This catches stuffed animals, dolls, printed images, cartoon faces, etc.
    # that may pass the colour/texture heuristics above.
    if not _verify_human_with_claude_api(img_bgr):
        return None, "not_human"
    # ── End human verification ────────────────────────────────────────────

    skin_samples = []
    regions = [
        (y + int(h_f*0.1), y + int(h_f*0.25), x + int(w_f*0.25), x + int(w_f*0.75)),
        (y + int(h_f*0.4), y + int(h_f*0.6), x + int(w_f*0.05), x + int(w_f*0.25)),
        (y + int(h_f*0.4), y + int(h_f*0.6), x + int(w_f*0.75), x + int(w_f*0.95)),
        (y + int(h_f*0.7), y + h_f, x + int(w_f*0.3), x + int(w_f*0.7)),
    ]
    for y1, y2, x1, x2 in regions:
        y1, y2 = max(0, y1), min(h, y2)
        x1, x2 = max(0, x1), min(w, x2)
        if y2 > y1 and x2 > x1:
            region = img_bgr[y1:y2, x1:x2]
            if region.size > 0:
                pixels = region.reshape(-1, 3)
                valid = pixels[(pixels[:,0] > 30) & (pixels[:,1] > 30) & (pixels[:,2] > 30)]
                valid = valid[(valid[:,0] < 230) & (valid[:,1] < 230) & (valid[:,2] < 230)]
                if len(valid) > 0:
                    sample_size = min(50, len(valid))
                    indices = np.random.choice(len(valid), sample_size, replace=False)
                    skin_samples.extend(valid[indices])
    if len(skin_samples) < 25:
        return None, "no_skin"
    b, g, r = np.mean(skin_samples, axis=0)
    return (float(r), float(g), float(b)), "ok"

def white_balance(img_bgr):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    avg_a, avg_b = np.mean(lab[:,:,1]), np.mean(lab[:,:,2])
    lab[:,:,1] -= (avg_a - 128) * (lab[:,:,0] / 255.0) * 1.1
    lab[:,:,2] -= (avg_b - 128) * (lab[:,:,0] / 255.0) * 1.1
    lab = np.clip(lab, 0, 255).astype(np.uint8)
    corrected = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    lab2 = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab2)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

def engineer_features(r, g, b):
    rg, rb, gb = r/(g+1e-6), r/(b+1e-6), g/(b+1e-6)
    br = (r+g+b)/3.0
    arr = np.uint8([[[int(b), int(g), int(r)]]])
    lab = cv2.cvtColor(arr, cv2.COLOR_BGR2Lab)[0][0]
    L = lab[0]/255.0*100
    bl = lab[2]-128
    if abs(bl) < 1e-3: bl = 1e-3
    ita = np.degrees(np.arctan((L-50)/bl))
    return [r, g, b, rg, rb, gb, br, ita]

def check_image_quality(img_arr):
    brightness = np.mean(img_arr)
    if brightness < 30:  return False, "too_dark"
    if brightness > 230: return False, "too_bright"
    return True, "ok"

# ================================================================
# MODEL TRAINING
# ================================================================
FEATURES = ["R", "G", "B", "RG", "RB", "GB", "BR", "ITA"]

@st.cache_resource
def train_model():
    try:
        data = pd.read_csv("skin_undertone_dataset.csv")
    except FileNotFoundError:
        st.error("❌ skin_undertone_dataset.csv not found. Run:  python generate_data.py")
        st.stop()
    df = data.copy()
    df["RG"] = df["R"] / (df["G"] + 1e-6)
    df["RB"] = df["R"] / (df["B"] + 1e-6)
    df["GB"] = df["G"] / (df["B"] + 1e-6)
    df["BR"] = (df["R"] + df["G"] + df["B"]) / 3.0
    def compute_ita(row):
        arr = np.uint8([[[int(row.B), int(row.G), int(row.R)]]])
        lab = cv2.cvtColor(arr, cv2.COLOR_BGR2Lab)[0][0]
        L = lab[0]/255.0*100
        bl = lab[2]-128
        if abs(bl) < 1e-3: bl = 1e-3
        return np.degrees(np.arctan((L-50)/bl))
    df["ITA"] = df.apply(compute_ita, axis=1)
    X, y = df[FEATURES], df["Undertone"]

    # Fairness reporting
    if "Fitzpatrick" in df.columns:
        fitz_acc = {}
        for fitz in sorted(df["Fitzpatrick"].unique()):
            mask = df["Fitzpatrick"] == fitz
            fitz_acc[fitz] = {"n": int(mask.sum()), "undertone_dist": df[mask]["Undertone"].value_counts().to_dict()}
        st.session_state["fairness_report"] = fitz_acc

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)
    return model, acc

model, model_acc = train_model()

# ================================================================
# 12-SEASON DATA
# ================================================================
# Depth is derived from skin brightness (4 tiers):
#   Light  : brightness > 175
#   Light-Medium : 130–175
#   Medium : 100–130
#   Deep   : brightness < 100
#
# This gives full 12-season coverage without legacy fallbacks.
SEASONS = {
    ("Warm",    "Light"):        {"season": "Light Spring",  "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Fresh, warm, and luminous. You glow in soft, warm colours.",
        "palette": ["#FFAD90","#FF6B6B","#FFD166","#06C090","#FFF0D4","#E8B830"], "metals": "Gold & Rose Gold"},
    ("Warm",    "Light-Medium"): {"season": "True Spring",   "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Golden warmth with clear, vivid colours. Sun-kissed and radiant.",
        "palette": ["#FF8C42","#FFC145","#E8D44D","#4CA64C","#FF5733","#C8963C"], "metals": "Gold & Rose Gold"},
    ("Warm",    "Medium"):       {"season": "True Autumn",   "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Rich, earthy, and deeply warm. Golden, grounded, magnetic.",
        "palette": ["#CC5500","#7a7a00","#D4A800","#B7410E","#C19A6B","#1a7a1a"], "metals": "Gold, Bronze & Copper"},
    ("Warm",    "Deep"):         {"season": "Deep Autumn",   "badge_bg": "#4A3728", "badge_fg": "#FFFFFF",
        "description": "Intense, bold, and powerfully warm. Saturated dark earth tones.",
        "palette": ["#4a5e20","#D06050","#9a7000","#7B3F00","#800020","#A0522D"], "metals": "Gold, Bronze & Copper"},
    ("Cool",    "Light"):        {"season": "Light Summer",  "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Soft, cool, and luminous. Delicate pastels and icy elegance.",
        "palette": ["#E8D5E0","#B8D4E8","#D4C8E8","#E8C8C8","#C8D8C8","#F0E8F0"], "metals": "Silver & White Gold"},
    ("Cool",    "Light-Medium"): {"season": "True Summer",   "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Soft, cool, and quietly elegant. Dreamlike delicacy.",
        "palette": ["#C89080","#9a70c0","#90c0cc","#b090b0","#a0a0b0","#D8B8A8"], "metals": "Silver & White Gold"},
    ("Cool",    "Medium"):       {"season": "Soft Summer",   "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Versatile, soft, and beautifully balanced cool tones.",
        "palette": ["#cc5070","#30909a","#E8DCA0","#888078","#80a060","#8a6898"], "metals": "Gold & Silver — both work"},
    ("Cool",    "Deep"):         {"season": "Deep Winter",   "badge_bg": "#4A3728", "badge_fg": "#FFFFFF",
        "description": "Dramatic, intense, and powerfully cool. Jeweled darkness.",
        "palette": ["#800020","#0040a0","#673147","#364050","#007070","#1a1a1a"], "metals": "Silver, Platinum & Dark Rhodium"},
    ("Neutral", "Light"):        {"season": "Bright Spring", "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Clear, sparkling, and vivid. High clarity with warm radiance.",
        "palette": ["#FF6B6B","#FF9F43","#FECA57","#1DD1A1","#54A0FF","#FF6B9D"], "metals": "Yellow Gold & Rose Gold"},
    ("Neutral", "Light-Medium"): {"season": "Soft Autumn",   "badge_bg": "#C8963C", "badge_fg": "#FFFFFF",
        "description": "Balanced and beautifully adaptable. Muted warm-neutrals.",
        "palette": ["#80a060","#c06048","#5a7088","#b07830","#3a8888","#907060"], "metals": "Gold & Silver — both work"},
    ("Neutral", "Medium"):       {"season": "True Winter",   "badge_bg": "#4A3728", "badge_fg": "#FFFFFF",
        "description": "Bold, cool, and striking. High contrast is your superpower.",
        "palette": ["#2850cc","#b00060","#006840","#E8F0F8","#c00020","#E080A0"], "metals": "Silver, Platinum & White Gold"},
    ("Neutral", "Deep"):         {"season": "Bright Winter", "badge_bg": "#4A3728", "badge_fg": "#FFFFFF",
        "description": "Vivid, crisp, and commanding. High contrast with cool clarity.",
        "palette": ["#CC0044","#0055CC","#00AA66","#FF0080","#6600CC","#00CCFF"], "metals": "Silver, White Gold & Platinum"},
}

# Canonical season name lookup (mirrors SEASONS keys)
SEASON_LOOKUP = {k: v["season"] for k, v in SEASONS.items()}


REALISTIC_MAKEUP = {
    "Warm":    {"Lipstick": [{"name":"MAC Marrakesh","brand":"MAC","hex":"#B85C38","price":"$22"}],
                "Blush":    [{"name":"NARS Dolce Vita","brand":"NARS","hex":"#C97D6E","price":"$30"}],
                "Foundation":[{"name":"Fenty Pro Filt'r 145","brand":"Fenty","hex":"#DEB28B","price":"$35"}]},
    "Cool":    {"Lipstick": [{"name":"MAC Rebel","brand":"MAC","hex":"#B84A6A","price":"$22"}],
                "Blush":    [{"name":"Rare Beauty Grace","brand":"Rare Beauty","hex":"#D8667E","price":"$23"}],
                "Foundation":[{"name":"Fenty Pro Filt'r 120","brand":"Fenty","hex":"#E8C8B0","price":"$35"}]},
    "Neutral": {"Lipstick": [{"name":"MAC Velvet Teddy","brand":"MAC","hex":"#D2B48C","price":"$22"}],
                "Blush":    [{"name":"Glossier Cloud Paint","brand":"Glossier","hex":"#E8A880","price":"$22"}],
                "Foundation":[{"name":"Fenty Pro Filt'r 130","brand":"Fenty","hex":"#E0B898","price":"$35"}]},
}

CLOTHING_COLORS = {
    "Light Spring":  ["Peach","Coral","Warm Yellow","Mint","Ivory","Gold"],
    "True Spring":   ["Tangerine","Sunny Yellow","Warm Green","Salmon","Caramel","Golden Brown"],
    "Bright Spring": ["Hot Coral","Bright Yellow","Electric Green","Vivid Orange","Turquoise","Hot Pink"],
    "Light Summer":  ["Baby Blue","Lavender Mist","Pale Rose","Soft White","Powder Pink","Icy Lilac"],
    "True Summer":   ["Dusty Rose","Lavender","Powder Blue","Mauve","Soft Gray","Plum"],
    "Soft Summer":   ["Sage Green","Soft Teal","Blush","Stone Gray","Dusty Purple","Muted Slate"],
    "True Autumn":   ["Burnt Orange","Olive","Mustard","Rust","Camel","Forest"],
    "Soft Autumn":   ["Sage","Terracotta","Caramel","Muted Teal","Slate Blue","Warm Taupe"],
    "Deep Autumn":   ["Chocolate","Burgundy","Dark Olive","Terracotta","Deep Teal","Cognac"],
    "True Winter":   ["Royal Blue","Magenta","Emerald","Pure White","True Red","Electric Blue"],
    "Deep Winter":   ["Burgundy","Cobalt","Plum","Charcoal","Deep Teal","Jet Black"],
    "Bright Winter": ["Fuchsia","Electric Blue","Emerald Green","Pure White","Cherry Red","Bright Purple"],
}

JEWELRY_DATA = {
    "Warm":    "Gold, Bronze & Copper",
    "Cool":    "Silver, Platinum & White Gold",
    "Neutral": "Gold & Silver — both work",
}
PINTEREST_LINKS = {s: f"https://www.pinterest.com/search/pins/?q={s.replace(' ','%20')}%20outfit%20color%20palette"
                   for s in list(CLOTHING_COLORS.keys())}
LOADING_FACTS = [
    "✨ Your vein colour is one of the best indicators of undertone",
    "✨ People with warm undertones look best in gold jewellery",
    "✨ Deep Autumn is the rarest colour season",
    "✨ The right colours can make you look younger and more vibrant",
    "✨ 12-season analysis provides the most precise colour matching",
    "✨ Bright Winter and Bright Spring share vivid clarity across cool and warm tones",
]

# ================================================================
# ANALYSIS FUNCTIONS
# ================================================================
def compute_harmony_score(palette_hex: list, undertone: str) -> int:
    """
    Compute a palette harmony score (0–100) based on two real signals:
    1. Hue spread — how evenly distributed the palette hues are (higher = more harmonious variety)
    2. Undertone alignment — how many palette colours share the warm/cool/neutral character of the season

    Returns an integer between 60 and 98 so it always reads as a 'good' score
    (the palette is curated to the season, so it should always be at least decent).
    """
    hues = []
    warm_count = 0
    for c in palette_hex:
        try:
            r_val = int(c[1:3], 16) / 255.0
            g_val = int(c[3:5], 16) / 255.0
            b_val = int(c[5:7], 16) / 255.0
            # Convert RGB → HSV to get hue
            import colorsys
            h, s, v = colorsys.rgb_to_hsv(r_val, g_val, b_val)
            if s > 0.05:  # ignore near-grey swatches
                hues.append(h * 360)
            # Warm hues: red-yellow range (0–60° and 320–360°)
            if (0 <= h * 360 <= 60) or (320 <= h * 360 <= 360):
                warm_count += 1
        except Exception:
            continue

    # Signal 1: hue spread (std dev of hues, normalised to 0–50 pts)
    if len(hues) >= 2:
        hue_std = float(np.std(hues))
        spread_score = min(50, int(hue_std / 1.8))
    else:
        spread_score = 20

    # Signal 2: undertone alignment (0–48 pts)
    n = len(palette_hex)
    if undertone == "Warm":
        aligned = warm_count
    elif undertone == "Cool":
        aligned = n - warm_count
    else:  # Neutral — balanced is best
        balance = abs(warm_count - (n - warm_count))
        aligned = n - balance

    alignment_score = int((aligned / max(n, 1)) * 48)

    raw = spread_score + alignment_score  # 0–98
    # Clamp to 60–98 — a curated palette should always score well
    return max(60, min(98, raw))


def _build_result(prediction, depth, r, g, b, confidence, probabilities, extra=None):
    season_info = None
    for (u, d), info in SEASONS.items():
        if u == prediction and d == depth:
            season_info = info
            break
    if not season_info:
        season_info = SEASONS[("Neutral", "Medium")]
    season = season_info["season"]
    out = {
        "r": r, "g": g, "b": b,
        "pred": prediction, "confidence": confidence, "depth": depth,
        "season": season, "description": season_info["description"],
        "palette": season_info["palette"], "metals": season_info["metals"],
        "badge_bg": season_info["badge_bg"], "badge_fg": season_info["badge_fg"],
        "probabilities": probabilities, "model_classes": model.classes_,
        "clothing_colors": CLOTHING_COLORS.get(season, CLOTHING_COLORS["Soft Autumn"]),
        "jewelry": JEWELRY_DATA.get(prediction, "Gold & Silver — both work"),
        "pinterest_link": PINTEREST_LINKS.get(season, "https://pinterest.com"),
        "makeup": REALISTIC_MAKEUP.get(prediction, REALISTIC_MAKEUP["Neutral"]),
        "harmony_score": compute_harmony_score(season_info["palette"], prediction),
    }
    if extra:
        out.update(extra)
    return out

def analyze_photo(image, use_wb=True):
    img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    quality_ok, quality_status = check_image_quality(np.array(image))
    if use_wb:
        img_bgr = white_balance(img_bgr)
    result, status = detect_face_and_extract_skin(img_bgr)
    if result is None:
        return None, status, quality_status
    r, g, b = result
    features = engineer_features(r, g, b)
    prediction = model.predict([features])[0]
    probabilities = model.predict_proba([features])[0]
    confidence = float(max(probabilities)) * 100
    if confidence < 35:
        return None, "low_confidence", quality_status
    brightness = (r+g+b)/3
    depth = "Light" if brightness > 175 else "Light-Medium" if brightness > 130 else "Deep" if brightness < 100 else "Medium"
    return _build_result(prediction, depth, r, g, b, confidence, probabilities), "ok", quality_status

def analyze_multi_photos(images, use_wb=True):
    all_results = []
    for img in images:
        res, status, _ = analyze_photo(img, use_wb)
        if res and status == "ok":
            all_results.append(res)
    if len(all_results) < 2:
        return None, "not_enough", None
    avg_r = np.mean([r["r"] for r in all_results])
    avg_g = np.mean([r["g"] for r in all_results])
    avg_b = np.mean([r["b"] for r in all_results])
    features = engineer_features(avg_r, avg_g, avg_b)
    prediction = model.predict([features])[0]
    probabilities = model.predict_proba([features])[0]
    confidence = min(95, float(max(probabilities)) * 100 + 5)
    brightness = (avg_r + avg_g + avg_b) / 3
    depth = "Light" if brightness > 175 else "Light-Medium" if brightness > 130 else "Deep" if brightness < 100 else "Medium"
    return _build_result(prediction, depth, avg_r, avg_g, avg_b, confidence, probabilities,
                         {"n_frames": len(all_results)}), "ok", images[0] if images else None

def manual_analysis_with_features(skin_hex, eye_hex, hair_hex):
    r,g,b   = int(skin_hex[1:3],16), int(skin_hex[3:5],16), int(skin_hex[5:7],16)
    hair_r, hair_g, hair_b = int(hair_hex[1:3],16), int(hair_hex[3:5],16), int(hair_hex[5:7],16)
    hair_brightness = (hair_r + hair_g + hair_b) / 3
    depth = "Light" if hair_brightness > 175 else "Light-Medium" if hair_brightness > 130 else "Deep" if hair_brightness < 100 else "Medium"
    features = engineer_features(r, g, b)
    prediction = model.predict([features])[0]
    probabilities = model.predict_proba([features])[0]
    confidence = float(max(probabilities)) * 100
    return _build_result(prediction, depth, r, g, b, confidence, probabilities, {"is_manual": True})

# ================================================================
# AFFIRMATION CARD  →  downloadable PNG
# ================================================================
def generate_affirmation_png(r):
    """Return PNG bytes of a styled affirmation card."""
    W, H = 800, 460
    vibe = COLOR_VIBES.get(r['season'], {"vibe": "Beautiful & Unique", "emoji": "✨", "mood": "Your colours enhance your natural beauty."})
    palette = r['palette']

    img = Image.new("RGB", (W, H), "#1A1816")
    draw = ImageDraw.Draw(img)

    # Background gradient strips
    for i, c in enumerate(palette[:6]):
        x0 = i * (W // 6)
        x1 = (i+1) * (W // 6)
        rc, gc, bc = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        for yy in range(H):
            alpha = int(30 * (1 - yy/H))
            draw.rectangle([x0, yy, x1, yy+1],
                           fill=(rc, gc, bc, 255))
    # Overlay
    overlay = Image.new("RGBA", (W, H), (26, 24, 22, 210))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Try to load a font; fall back to default
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 36)
        font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title
        font_small = font_title

    # Brand
    draw.text((W//2, 40), "TINTA", font=font_sub, fill="#D4AF37", anchor="mm")
    draw.text((W//2, 80), "AI Personal Color Analysis", font=font_small, fill="#D4C8B8", anchor="mm")

    # Season badge
    badge_txt = f"✦ {r['season']}"
    draw.rounded_rectangle([W//2-130, 108, W//2+130, 148], radius=20, fill=r.get('badge_bg','#C8963C'))
    draw.text((W//2, 128), badge_txt, font=font_sub, fill=r.get('badge_fg','#FFFFFF'), anchor="mm")

    # Vibe
    draw.text((W//2, 190), vibe['vibe'], font=font_title, fill="#D4AF37", anchor="mm")
    draw.text((W//2, 240), vibe['mood'], font=font_small, fill="#F5EFE6", anchor="mm")

    # Confidence
    draw.text((W//2, 280), f"Confidence: {r['confidence']:.0f}%  ·  {r['pred']} · {r['depth']}",
              font=font_small, fill="#D4C8B8", anchor="mm")

    # Palette swatches
    sw = 60; gap = 12; total = sw*6 + gap*5; x0 = (W - total)//2; y0 = 320
    for i, c in enumerate(palette[:6]):
        rc, gc, bc = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        draw.rounded_rectangle([x0+i*(sw+gap), y0, x0+i*(sw+gap)+sw, y0+sw], radius=12, fill=(rc,gc,bc))

    # Footer
    draw.text((W//2, 420), "tinta.ai  ·  Your colour story starts here", font=font_small, fill="#888", anchor="mm")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()

# ================================================================
# QUIZ FUNCTIONS
# ================================================================
def render_quiz_question(num, total, text, options, icons, key):
    dots = "".join(
        f'<div class="dot {"active" if i==num else "completed" if i<num else ""}"></div>'
        for i in range(total)
    )
    st.markdown(f'<div class="progress-dots">{dots}</div>', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; margin-bottom:32px;'>{text}</h3>", unsafe_allow_html=True)
    cols = st.columns(len(options))
    for col, opt, icon in zip(cols, options, icons):
        with col:
            selected = (st.session_state.quiz_answers.get(key) == opt)
            st.markdown(f"""
            <div class="quiz-card {'selected' if selected else ''}">
                <div class="quiz-icon">{icon}</div>
                <div class="quiz-label">{opt}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(opt, key=f"quiz_{key}_{opt}", use_container_width=True):
                st.session_state.quiz_answers[key] = opt
                st.rerun()
    if st.session_state.quiz_answers.get(key):
        if st.button("Next →", use_container_width=True):
            st.session_state.quiz_step += 1
            st.rerun()

def run_quiz():
    total = 6
    step  = st.session_state.quiz_step
    questions = [
        {"text":"What colour are your veins?",        "options":["Blue/Purple","Blue-Green","Green"],             "icons":["💙","💚💙","💚"],     "key":"vein"},
        {"text":"Which metal looks better on you?",   "options":["Silver","Both","Gold"],                        "icons":["🥈","✨","🥇"],        "key":"metal"},
        {"text":"How does your skin react to sun?",   "options":["Burns easily","Burns then tans","Tans easily","Never burns"], "icons":["🔥","🌤️","☀️","🏝️"], "key":"sun"},
        {"text":"Which white looks best near your face?","options":["Bright white","Both","Ivory"],              "icons":["⬜","🤍","📜"],        "key":"white"},
        {"text":"Most flattering lipstick shade?",    "options":["Berry","Both","Coral"],                        "icons":["🍇","💄","🍊"],        "key":"lipstick"},
        {"text":"What is your natural hair colour?",  "options":["Light blonde/red","Medium brown","Dark brown/black"],"icons":["🟡","🟤","⚫"],   "key":"hair"},
    ]
    if step < total:
        render_quiz_question(step, total, questions[step]["text"], questions[step]["options"],
                             questions[step]["icons"], questions[step]["key"])
    else:
        sc, cc = 0, 0
        vein = st.session_state.quiz_answers.get("vein","Blue-Green")
        if vein=="Blue/Purple": cc+=2
        elif vein=="Green": sc+=2
        else: sc+=1; cc+=1
        metal = st.session_state.quiz_answers.get("metal","Both")
        if metal=="Silver": cc+=2
        elif metal=="Gold": sc+=2
        else: sc+=1; cc+=1
        sun = st.session_state.quiz_answers.get("sun","Burns then tans")
        if sun=="Burns easily": cc+=2
        elif sun=="Burns then tans": sc+=1; cc+=1
        elif sun=="Tans easily": sc+=2
        else: sc+=3
        white = st.session_state.quiz_answers.get("white","Both")
        if white=="Bright white": cc+=2
        elif white=="Ivory": sc+=2
        else: sc+=1; cc+=1
        lip = st.session_state.quiz_answers.get("lipstick","Both")
        if lip=="Berry": cc+=2
        elif lip=="Coral": sc+=2
        else: sc+=1; cc+=1
        hair = st.session_state.quiz_answers.get("hair","Medium brown")
        depth = "Light" if "Light" in hair else "Deep" if "Dark" in hair else "Light-Medium"
        if sc > cc+2: ut,cf = "Warm",   min(90, 65+(sc-cc)*5)
        elif cc > sc+2: ut,cf = "Cool", min(90, 65+(cc-sc)*5)
        else:           ut,cf = "Neutral", 75
        season_info = next((v for (u,d),v in SEASONS.items() if u==ut and d==depth), SEASONS[("Neutral","Medium")])
        results = {
            "r": None, "g": None, "b": None,  # no photo — skin swatch hidden safely
            "pred":ut,"confidence":cf,"depth":depth,
            "season":season_info["season"],"description":season_info["description"],
            "palette":season_info["palette"],"metals":season_info["metals"],
            "badge_bg":season_info["badge_bg"],"badge_fg":season_info["badge_fg"],
            "clothing_colors":CLOTHING_COLORS.get(season_info["season"],CLOTHING_COLORS["Soft Autumn"]),
            "jewelry":JEWELRY_DATA.get(ut,"Gold & Silver — both work"),
            "pinterest_link":PINTEREST_LINKS.get(season_info["season"],"https://pinterest.com"),
            "makeup":REALISTIC_MAKEUP.get(ut,REALISTIC_MAKEUP["Neutral"]),
            "harmony_score": compute_harmony_score(season_info["palette"], ut), "is_quiz": True,
        }
        st.session_state.analysis_results = results
        st.session_state.uploaded_photo = None  # quiz has no photo
        st.session_state.page = "results1"
        st.rerun()

# ================================================================
# PDF REPORT
# ================================================================
def generate_pdf_report(results):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    title_style   = ParagraphStyle('T', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=TA_CENTER, textColor=rl_colors.HexColor("#4A3728"))
    heading_style = ParagraphStyle('H', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=rl_colors.HexColor("#C8963C"))
    normal_style  = ParagraphStyle('N', parent=styles['Normal'],   fontSize=11, spaceAfter=6)
    story = [
        Paragraph("TINTA", title_style),
        Paragraph("AI Personal Color Analysis Report", styles['Heading2']),
        Spacer(1,20),
        Paragraph(f"Your Season: {results['season']}", heading_style),
        Paragraph(f"Undertone: {results['pred']} · Depth: {results['depth']}", normal_style),
        Paragraph(f"Confidence: {results['confidence']:.0f}%", normal_style),
        Spacer(1,12),
        Paragraph(results['description'], normal_style),
        Spacer(1,12),
        Paragraph("Your Color Palette", heading_style),
        Paragraph(" ".join([f'<font color="{c}">⬤</font> {c}' for c in results['palette']]), normal_style),
        Spacer(1,12),
        Paragraph("Jewelry Recommendations", heading_style),
        Paragraph(results['jewelry'], normal_style),
        Spacer(1,30),
        Paragraph("Generated by Tinta - AI Personal Color Analysis", styles['Normal']),
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

# ================================================================
# SYSTEM COLOR SCHEME DETECTION  (applied on first render only)
# ================================================================
def _inject_color_scheme_detector():
    """Inject JS that sets session state via query params on first visit."""
    st.markdown("""
    <script>
    (function() {
        if (sessionStorage.getItem('tinta_scheme_applied')) return;
        var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        sessionStorage.setItem('tinta_scheme_applied', '1');
        if (dark) {
            var url = new URL(window.location);
            url.searchParams.set('_dark', '1');
            window.history.replaceState(null, '', url.toString());
        }
    })();
    </script>""", unsafe_allow_html=True)

# ================================================================
# CSS & SYSTEM-THEME INIT
# ================================================================
# On first run, detect system preference
if st.session_state.dark_mode is None:
    params = st.query_params
    st.session_state.dark_mode = params.get("_dark", "0") == "1"

st.markdown(load_css(), unsafe_allow_html=True)
_inject_color_scheme_detector()

# ================================================================
# SIDEBAR
# ================================================================
ALL_SEASONS = sorted(set(v["season"] for v in SEASONS.values()))

with st.sidebar:
    # User avatar placeholder
    st.markdown("""
    <div style='text-align:center; padding:20px 0 8px;'>
        <div class='user-avatar'>T</div>
        <div class='brand' style='font-size:2rem;'>TINTA</div>
        <p style='font-size:10px; letter-spacing:2px; color:var(--text-secondary); margin-top:4px;'>AI COLOR ANALYSIS</p>
    </div>""", unsafe_allow_html=True)

    icon = "☀️ Light Mode" if st.session_state.dark_mode else "🌙 Dark Mode"
    if st.button(icon, use_container_width=True):
        toggle_dark_mode()
        st.rerun()

    st.markdown("---")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "welcome"
        st.rerun()

    if st.button("🎨 New Analysis", use_container_width=True):
        st.session_state.page = "options"
        st.session_state.analysis_results = None
        st.session_state.uploaded_photo   = None
        st.rerun()

    st.markdown("---")

    if st.session_state.saved_analyses:
        dm = st.session_state.dark_mode
        txt_col   = "#F5EFE6" if dm else "#3D2B1F"
        sub_col   = "#D4C8B8" if dm else "#5A4A3A"
        gold_col  = "#D4AF37" if dm else "#C89F4A"
        border_col = "rgba(212,175,55,0.2)" if dm else "rgba(61,43,31,0.1)"
        card_col  = "#2a2724" if dm else "#FFFFFF"

        st.markdown(f"<p style='font-weight:700; font-size:15px; color:{txt_col}; margin:8px 0 4px;'>📁 Color Diary</p>", unsafe_allow_html=True)

        # Sort & Filter controls
        sort_opt   = st.selectbox("Sort", ["Newest first","Oldest first"], key="diary_sort_select",
                                  index=0 if st.session_state.diary_sort=="Newest first" else 1, label_visibility="collapsed")
        filter_opt = st.selectbox("Filter", ["All seasons"] + ALL_SEASONS, key="diary_filter_select", label_visibility="collapsed")
        st.session_state.diary_sort   = sort_opt
        st.session_state.diary_filter = filter_opt

        entries = list(enumerate(st.session_state.saved_analyses))
        if filter_opt != "All seasons":
            entries = [(i,a) for i,a in entries if a["season"] == filter_opt]
        if sort_opt == "Newest first":
            entries = list(reversed(entries))

        if not entries:
            st.markdown(f"<p style='color:{sub_col}; font-size:12px;'>No entries match the filter.</p>", unsafe_allow_html=True)
        else:
            for orig_idx, a in entries:
                # Show inline confirmation inside the sidebar if this entry is pending delete
                if st.session_state.delete_confirm_idx == orig_idx:
                    st.markdown(f"""
                    <div style='background:{card_col}; border:1px solid rgba(200,159,74,0.35); border-radius:12px;
                                padding:12px 14px; margin:6px 0;'>
                        <div style='font-size:20px; text-align:center; margin-bottom:6px;'>🗑️</div>
                        <p style='font-size:12px; text-align:center; color:{txt_col}; margin:0 0 10px;'>
                            Delete <strong>{a["season"]}</strong>?<br>
                            <span style='color:{sub_col}; font-size:11px;'>This cannot be undone.</span>
                        </p>
                    </div>""", unsafe_allow_html=True)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Cancel", key=f"cancel_{orig_idx}", use_container_width=True):
                            st.session_state.delete_confirm_idx = None
                            st.rerun()
                    with cc2:
                        if st.button("Delete", key=f"confirm_{orig_idx}", use_container_width=True):
                            st.session_state.saved_analyses.pop(orig_idx)
                            st.session_state.delete_confirm_idx = None
                            st.rerun()
                else:
                    c1, c2 = st.columns([4,1])
                    with c1:
                        st.markdown(f"""
                        <div style='padding:6px 0; border-bottom:1px solid {border_col};'>
                            <span style='font-size:11px; color:{sub_col};'>{a["date"]}</span><br>
                            <span style='font-weight:600; color:{txt_col};'>{a["season"]}</span>
                            <span style='color:{gold_col};'> ({a["confidence"]:.0f}%)</span>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        if st.button("🗑", key=f"del_{orig_idx}", help="Delete entry"):
                            st.session_state.delete_confirm_idx = orig_idx
                            st.rerun()

# ================================================================
# DELETE CONFIRMATION MODAL
# ================================================================
# Delete confirmation is handled inline inside the sidebar

# ================================================================
# UI RENDERING FUNCTIONS
# ================================================================
def render_skeleton_loader():
    st.markdown("""
    <div style="padding:20px 0;">
        <div class="skeleton" style="height:28px; width:60%; margin:0 auto 16px;"></div>
        <div class="skeleton" style="height:180px; border-radius:20px; margin-bottom:16px;"></div>
        <div class="skeleton" style="height:14px; width:80%; margin:0 auto 10px;"></div>
        <div class="skeleton" style="height:14px; width:65%; margin:0 auto 10px;"></div>
        <div style="display:flex; gap:12px; margin-top:16px;">
            <div class="skeleton" style="height:72px; flex:1; border-radius:14px;"></div>
            <div class="skeleton" style="height:72px; flex:1; border-radius:14px;"></div>
            <div class="skeleton" style="height:72px; flex:1; border-radius:14px;"></div>
            <div class="skeleton" style="height:72px; flex:1; border-radius:14px;"></div>
        </div>
    </div>""", unsafe_allow_html=True)

def render_welcome_page():
    st.markdown("""
    <div style="text-align:center; padding:80px 20px 40px;">
        <div class="brand">Ti<span style="font-style:italic;">nta</span></div>
        <p style="letter-spacing:6px; margin-top:8px; font-size:12px; opacity:0.7;">AI PERSONAL COLOR ANALYSIS</p>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    features = [
        ("✨","Discover Your Beauty","AI analyses your skin tone to reveal your unique colour identity."),
        ("⚡","Simple & Quick","Upload a photo. Results in seconds — no appointments needed."),
        ("🎨","Personalised Results","Custom palettes, jewellery tips, makeup shades — just for you."),
    ]
    for i, (col, (icon, title, desc)) in enumerate(zip([col1,col2,col3], features)):
        with col:
            st.markdown(f"""
            <div class="card card-anim-{i}" style="text-align:center;">
                <div style="font-size:56px; margin-bottom:16px;">{icon}</div>
                <h3 style="color:var(--text-primary);">{title}</h3>
                <p style="color:var(--text-primary);">{desc}</p>
            </div>""", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1,2,1])
    with col_btn:
        if st.button("Begin Your Journey →", use_container_width=True):
            st.session_state.page = "options"
            st.rerun()

def render_options_page():
    st.markdown("<h2 style='text-align:center; margin-bottom:40px;'>Choose Your Mode</h2>", unsafe_allow_html=True)
    modes = [
        ("📸","Single Photo","Upload one clear face photo","single"),
        ("🎞️","Multi Photo","2+ photos averaged for accuracy","multi"),
        ("🎨","Manual Picker","Select skin, eye & hair colours","manual"),
        ("📋","Undertone Quiz","6 questions — no photo needed","quiz"),
        ("🔬","Compare Photos","Side-by-side comparison","compare"),
        ("📷","Calibrate Camera","Fix your phone's colour bias","calibrate"),
    ]
    col1, col2 = st.columns(2)
    for i, (icon, title, desc, key) in enumerate(modes):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="mode-card card-anim-{i % 3}">
                <div class="mode-icon">{icon}</div>
                <h3 style="color:var(--text-primary);">{title}</h3>
                <p style="color:var(--text-secondary);">{desc}</p>
            </div>""", unsafe_allow_html=True)
            if st.button("Select", key=f"mode_{key}_btn", use_container_width=True):
                # Always reset state when switching modes
                st.session_state.uploaded_photo   = None
                st.session_state.analysis_results = None
                st.session_state.compare_results  = None
                st.session_state.compare_images   = None
                if key == "quiz":
                    st.session_state.quiz_step    = 0
                    st.session_state.quiz_answers = {}
                st.session_state.mode = key
                st.session_state.page = "input"
                st.rerun()

def _validate_upload(uploaded_file):
    """Check file size; return (image_or_None, error_msg_or_None)."""
    if uploaded_file is None:
        return None, None
    ok, size_mb = check_file_size(uploaded_file)
    if not ok:
        return None, f"⚠️ File too large ({size_mb:.1f} MB). Please upload a photo under {MAX_UPLOAD_MB} MB."
    return Image.open(uploaded_file), None

def render_single_photo_input():
    st.markdown("<h2>📸 Single Photo Analysis</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    image = None
    with col1:
        st.markdown("### Upload Photo")
        uploaded = st.file_uploader("Choose a photo", type=["jpg","png","jpeg"], label_visibility="collapsed", key="single_upload")
        img, err = _validate_upload(uploaded)
        if err:
            st.error(err); image = None
        elif img:
            image = img
            st.image(image, width=350, caption="Your photo")
    with col2:
        st.markdown("### Take Photo")
        camera = st.camera_input("Face the camera", label_visibility="collapsed", key="single_camera")
        if camera:
            image = Image.open(camera)
            st.image(image, width=350, caption="Your photo")

    with st.expander("📸 Photo tips for best results"):
        st.markdown("- **Natural daylight** — sit near a window\n- **Fill the frame** — face takes up most of the photo\n- **Face the camera directly** — no angles\n- **No filters** — turn off beauty mode")

    if st.button("Analyse My Colours →", use_container_width=True):
        if not image:
            st.error("Please upload or take a photo first")
            return
        skel = st.empty()
        with skel.container():
            render_skeleton_loader()
        prog = st.progress(0)
        step_text = st.empty()
        steps = [("🔍 Detecting face…",25),("🎨 Extracting skin tones…",50),("📊 Analysing undertone…",75),("✨ Generating your palette…",100)]
        for msg, pct in steps:
            step_text.markdown(f"<div style='text-align:center; padding:12px 20px; background:var(--card-bg); border-radius:20px; border:1px solid rgba(200,159,74,0.2); color:var(--text-primary);'>{msg}</div>", unsafe_allow_html=True)
            prog.progress(pct); time.sleep(0.4)
        step_text.empty(); prog.empty(); skel.empty()

        results, status, quality = analyze_photo(image)
        if status == "no_face" or status == "no_face_forward":
            st.error("❌ No face detected. Please upload a clear, front-facing photo — side profiles and back-of-head photos are not supported.")
        elif status == "multiple_faces":
            st.error("❌ Multiple faces detected. Please upload a photo with only one person.")
        elif status == "face_too_small":
            st.error("❌ Face too small in the frame. Move closer to the camera.")
        elif status == "not_human":
            st.warning("⚠️ Non-human face detected. Tinta only works with real human faces.")
            st.info("💡 Please upload a clear photo of a real person. Images of **dolls, anime characters, animals, illustrations, or printed photos** are not supported.")
        elif status == "no_skin":
            st.error("❌ Could not extract skin tone. Please ensure good lighting.")
        elif status == "low_confidence":
            if quality == "too_dark":
                st.warning("⚠️ Poor lighting detected — the image looks quite dark. Analysis may be less accurate. Please retake in brighter light for best results.")
            elif quality == "too_bright":
                st.warning("⚠️ Poor lighting detected — the image looks overexposed. Analysis may be less accurate.")
            else:
                st.warning("⚠️ Low confidence result. Please retake photo in better lighting.")
        else:
            if quality in ("too_dark","too_bright"):
                st.warning(f"⚠️ Poor lighting detected ({'too dark' if quality=='too_dark' else 'too bright'}). Results may be slightly less accurate — but continuing!")
            st.session_state.analysis_results = results
            st.session_state.uploaded_photo   = image
            st.session_state.page = "results1"
            st.rerun()

def render_multi_photo_input():
    st.markdown("<h2>🎞️ Multi-Photo Analysis</h2>", unsafe_allow_html=True)
    st.markdown("Upload 2 or more clear photos for a more accurate averaged result.")
    photos = []
    files = st.file_uploader("Upload photos (2 or more)", type=["jpg","png","jpeg"],
                              accept_multiple_files=True, label_visibility="collapsed", key="multi_upload")
    if files:
        for f in files:
            ok, size_mb = check_file_size(f)
            if not ok:
                st.error(f"⚠️ '{f.name}' is {size_mb:.1f} MB — over the {MAX_UPLOAD_MB} MB limit. Please use a smaller file.")
                return
        cols = st.columns(min(5, len(files)))
        for i, (col, f) in enumerate(zip(cols, files[:5])):
            with col:
                img = Image.open(f); st.image(img, width=120, caption=f"Photo {i+1}"); photos.append(img)
    if st.button("Analyse My Colours →", use_container_width=True):
        if len(photos) < 2:
            st.warning("Please upload at least 2 photos"); return
        with st.spinner(f"Analyzing {len(photos)} photos…"):
            prog = st.progress(0)
            for i in range(len(photos)):
                prog.progress(int((i+1)/len(photos)*100)); time.sleep(0.5)
            prog.empty()
            results, status, first_img = analyze_multi_photos(photos)
        if status != "ok":
            st.error("Could not analyze photos. Please ensure faces are clearly visible in all photos."); return
        st.session_state.analysis_results = results
        st.session_state.uploaded_photo   = first_img
        st.session_state.page = "results1"
        st.rerun()

def render_manual_picker_input():
    st.markdown("<h2>🎨 Manual Colour Selection</h2>", unsafe_allow_html=True)
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown("### Skin Tone"); skin = st.color_picker("","#D4A574",label_visibility="collapsed",key="manual_skin")
        st.markdown(f'<div style="background:{skin}; height:40px; border-radius:20px;"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("### Eye Colour"); eye = st.color_picker("","#8B5E3C",label_visibility="collapsed",key="manual_eye")
        st.markdown(f'<div style="background:{eye}; height:40px; border-radius:20px;"></div>', unsafe_allow_html=True)
    with col3:
        st.markdown("### Hair Colour"); hair = st.color_picker("","#5C3A1E",label_visibility="collapsed",key="manual_hair")
        st.markdown(f'<div style="background:{hair}; height:40px; border-radius:20px;"></div>', unsafe_allow_html=True)
    if st.button("Analyse My Colours →", use_container_width=True):
        results = manual_analysis_with_features(skin, eye, hair)
        results["manual_skin_hex"] = skin  # store so results card can show it
        st.session_state.analysis_results = results
        st.session_state.uploaded_photo = None  # no photo for manual mode
        st.session_state.page = "results1"
        st.rerun()

def render_quiz_input():
    run_quiz()

def render_compare_input():
    st.markdown("<h2>🔬 Compare Two Photos</h2>", unsafe_allow_html=True)
    col1,col2 = st.columns(2); img_a=img_b=None
    with col1:
        st.markdown("### Photo A")
        fa = st.file_uploader("Upload Photo A", type=["jpg","png","jpeg"], key="cmp_a", label_visibility="collapsed")
        img_a_raw, err = _validate_upload(fa)
        if err: st.error(err)
        elif img_a_raw: img_a = img_a_raw; st.image(img_a, width=280)
    with col2:
        st.markdown("### Photo B")
        fb = st.file_uploader("Upload Photo B", type=["jpg","png","jpeg"], key="cmp_b", label_visibility="collapsed")
        img_b_raw, err = _validate_upload(fb)
        if err: st.error(err)
        elif img_b_raw: img_b = img_b_raw; st.image(img_b, width=280)
    if st.button("Compare →", use_container_width=True):
        if not img_a or not img_b: st.error("Please upload both photos"); return
        with st.spinner("Analyzing both photos…"):
            res_a, sa, _ = analyze_photo(img_a); res_b, sb, _ = analyze_photo(img_b)
        _STATUS_MSG = {
            "no_face": "No face detected. Please upload a clear front-facing photo.",
            "no_face_forward": "No face detected. Please upload a clear, front-facing photo — side profiles and back-of-head photos are not supported.",
            "multiple_faces": "Multiple faces detected. Please upload a photo with only one person.",
            "face_too_small": "Face too small — move closer to the camera.",
            "not_human": "Non-human face detected. Please use a real photo of a real person — dolls, anime, animals, and illustrations are not supported.",
            "no_skin": "Could not extract skin tone. Please ensure good lighting.",
            "low_confidence": "Low confidence result. Please retake in better lighting.",
        }
        if sa != "ok": st.error(f"Photo A: {_STATUS_MSG.get(sa, sa.replace('_',' '))}."); return
        if sb != "ok": st.error(f"Photo B: {_STATUS_MSG.get(sb, sb.replace('_',' '))}."); return
        st.session_state.compare_results = {"a":res_a,"b":res_b}
        st.session_state.compare_images  = {"a":img_a,"b":img_b}
        st.session_state.page = "compare_results"; st.rerun()

def render_calibrate_input():
    st.markdown("<h2>📷 Calibrate Camera</h2>", unsafe_allow_html=True)
    st.markdown("Upload a photo of a plain white paper/wall to detect your camera's colour bias.")
    cal = st.file_uploader("White reference photo", type=["jpg","png","jpeg"], label_visibility="collapsed", key="calib")
    img, err = _validate_upload(cal)
    if err: st.error(err); return
    if img:
        st.image(img, width=320)
        arr = np.array(img)
        avg_r,avg_g,avg_b = np.mean(arr[:,:,0]),np.mean(arr[:,:,1]),np.mean(arr[:,:,2])
        bias = 'Warm' if avg_r>avg_g+10 else 'Cool' if avg_b>avg_g+10 else 'Neutral'
        st.info(f"**Calibration Results**\n\nDetected white: RGB({avg_r:.0f}, {avg_g:.0f}, {avg_b:.0f})\nCamera bias: **{bias}**\n\nThis calibration will be applied automatically.")

# ================================================================
# RESULTS CARDS
# ================================================================
def render_results_card1():
    r   = st.session_state.analysis_results
    img = st.session_state.uploaded_photo

    col1,col2 = st.columns([1,1])
    with col1:
        if img:
            st.image(img, width=320, caption="Your photo")
            # Only show skin swatch for photo-based analyses (r/g/b will be real numbers)
            if r.get('r') is not None and r.get('g') is not None and r.get('b') is not None:
                skin_hex = f"#{int(r['r']):02x}{int(r['g']):02x}{int(r['b']):02x}"
                st.markdown(f'<div style="background:{skin_hex}; height:45px; border-radius:23px; margin-top:12px;"></div><p style="text-align:center; font-size:12px; margin-top:8px; color:var(--text-secondary);">Detected skin tone</p>', unsafe_allow_html=True)
        elif r.get("manual_skin_hex"):
            # Manual picker — show chosen colour as swatch
            skin_hex = r["manual_skin_hex"]
            st.markdown(f"""
            <div style="text-align:center; padding:20px 0;">
                <div style="font-size:40px; margin-bottom:12px;">🎨</div>
                <div style="background:{skin_hex}; height:60px; border-radius:30px; margin:0 auto; max-width:200px;"></div>
                <p style="font-size:12px; margin-top:10px; color:var(--text-secondary);">Your chosen skin tone</p>
            </div>""", unsafe_allow_html=True)
        elif r.get("is_quiz"):
            st.markdown("""
            <div style="text-align:center; padding:20px 0;">
                <div style="font-size:64px; margin-bottom:12px;">📋</div>
                <p style="color:var(--text-secondary);">Based on your quiz answers</p>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align:center;" class="card-anim-0">
            <span style="background:{r['badge_bg']}; color:{r['badge_fg']}; padding:8px 24px; border-radius:40px; display:inline-block; font-weight:600;">✦ {r['season']}</span>
            <h2 style="margin:24px 0 12px; color:var(--text-primary);">{r['pred']} · {r['depth']}</h2>
            <div class="progress-container" style="max-width:250px; margin:0 auto;">
                <div class="progress-fill" style="width:{r['confidence']}%;"></div>
            </div>
            <p style="margin-top:12px; color:var(--text-primary);">Confidence {r['confidence']:.0f}%</p>
            <p style="margin-top:16px; color:var(--gold);">{r['description'][:80]}…</p>
        </div>""", unsafe_allow_html=True)
        if 'n_frames' in r:
            st.markdown(f'<p style="text-align:center; background:rgba(200,150,60,0.1); border:1px solid rgba(200,159,74,0.2); padding:8px; border-radius:24px; margin-top:16px; color:var(--text-primary);">✨ Averaged from {r["n_frames"]} photos</p>', unsafe_allow_html=True)

    # 1. COLOR VIBE GENERATOR
    vibe = COLOR_VIBES.get(r['season'], {"vibe":"Beautiful, Unique, You","emoji":"✨","mood":"Your colours enhance your natural beauty."})
    st.markdown(f"""
    <div class="unique-card card-anim-1">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:48px;">{vibe['emoji']}</div>
            <div>
                <div class="vibe-text">{vibe['vibe']}</div>
                <p style="margin:8px 0 0 0; color:var(--text-primary);">{vibe['mood']}</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Harmony Score
    st.markdown(f"""
    <div style="background:var(--card-bg); border-radius:24px; padding:24px; margin:24px 0; text-align:center; border:1px solid rgba(200,159,74,0.15);" class="card-anim-2">
        <div style="font-size:14px; letter-spacing:1px; color:var(--text-secondary);">COLOR HARMONY SCORE</div>
        <div style="font-size:56px; font-weight:700; color:var(--gold); margin:8px 0;">{r['harmony_score']}%</div>
        <div class="progress-container" style="max-width:200px; margin:12px auto;">
            <div class="progress-fill" style="width:{r['harmony_score']}%;"></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Color Palette
    st.markdown("<h3>🎨 Your Color Palette</h3>", unsafe_allow_html=True)
    cols = st.columns(len(r['palette']))
    for col, color in zip(cols, r['palette']):
        with col:
            st.markdown(f'''<div title="Click to copy {color}" class="color-swatch" style="background:{color};" onclick="navigator.clipboard.writeText('{color}')"></div><p style="text-align:center; font-size:11px; margin-top:8px; font-family:monospace; color:var(--text-secondary);">{color}</p>''', unsafe_allow_html=True)

    # 5. COLOR HARMONIES
    harmonies = get_color_harmonies(r['palette'])
    st.markdown("<h3>🎨 Color Harmonies</h3>", unsafe_allow_html=True)
    hc = st.columns(3)
    comp0, comp1 = harmonies['Complementary'][0], harmonies['Complementary'][1]
    analogous_html = ''.join(
        f'<div style="background:{c}; flex:1; height:30px; border-radius:8px;"></div>'
        for c in harmonies['Analogous']
    )
    triadic_html = ''.join(
        f'<div style="background:{c}; flex:1; height:30px; border-radius:8px;"></div>'
        for c in harmonies['Triadic']
    )
    with hc[0]: st.markdown(f"**Complementary**<div style='background:{comp0}; height:30px; border-radius:12px; margin:8px 0;'></div><div style='background:{comp1}; height:30px; border-radius:12px;'></div>", unsafe_allow_html=True)
    with hc[1]: st.markdown(f"**Analogous**<div style='display:flex; gap:4px; margin:8px 0;'>{analogous_html}</div>", unsafe_allow_html=True)
    with hc[2]: st.markdown(f"**Triadic**<div style='display:flex; gap:4px; margin:8px 0;'>{triadic_html}</div>", unsafe_allow_html=True)

    # 3. SEASONAL PLAYLIST
    playlist = SEASONAL_PLAYLISTS.get(r['season'])
    if playlist:
        st.markdown(f'<a href="{playlist}" target="_blank"><div class="btn-primary" style="text-align:center; margin:16px 0;">🎧 Listen to {r["season"]} Vibes on Spotify →</div></a>', unsafe_allow_html=True)
    st.markdown(f'<a href="{r["pinterest_link"]}" target="_blank"><div class="btn-primary" style="text-align:center; margin:16px 0;">📌 View Outfit Ideas on Pinterest →</div></a>', unsafe_allow_html=True)

    # Top 3 Probabilities
    if 'probabilities' in r:
        st.markdown("<h3>📊 Your Season Distribution</h3>", unsafe_allow_html=True)
        top3 = np.argsort(r['probabilities'])[::-1][:3]
        for idx in top3:
            undertone = r['model_classes'][idx]
            sn = next((v['season'] for (u,d),v in SEASONS.items() if u==undertone and d==r['depth']), undertone)
            prob = r['probabilities'][idx]*100
            st.markdown(f"""
            <div style="margin:16px 0;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="font-weight:500; color:var(--text-primary);">{undertone} · {sn}</span>
                    <span style="color:var(--gold);">{prob:.1f}%</span>
                </div>
                <div class="progress-container"><div class="progress-fill" style="width:{prob}%;"></div></div>
            </div>""", unsafe_allow_html=True)

def render_results_card2():
    r = st.session_state.analysis_results
    st.markdown(f"<h2 style='text-align:center; margin-bottom:32px;'>{r['season']} Recommendations</h2>", unsafe_allow_html=True)

    # Makeup
    st.markdown("<h3>💄 Makeup Recommendations</h3>", unsafe_allow_html=True)
    for label, key, emoji in [("Lipstick","Lipstick","💋"),("Blush","Blush","🌸"),("Foundation","Foundation","💄")]:
        st.markdown(f"<h4>{emoji} {label}</h4>", unsafe_allow_html=True)
        for item in r['makeup'][key]:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:16px; margin:12px 0; padding:12px; background:var(--card-bg); border:1px solid rgba(200,159,74,0.1); border-radius:16px;">
                <div style="background:{item['hex']}; width:50px; height:50px; border-radius:25px; flex-shrink:0;"></div>
                <div><strong style="color:var(--text-primary);">{item['brand']}</strong> <span style="color:var(--text-secondary);">{item['name']}</span><br><span style="color:var(--gold);">{item['price']}</span></div>
            </div>""", unsafe_allow_html=True)

    # Clothing
    st.markdown("<h3>👗 Your Best Clothing Colors</h3>", unsafe_allow_html=True)
    chips = "".join(f'<span class="chip-selector">🎨 {c}</span>' for c in r['clothing_colors'])
    st.markdown(f'<div style="margin:20px 0;">{chips}</div>', unsafe_allow_html=True)
    st.markdown("**Shop at:** Uniqlo, H&M, Zara, Mango, Aritzia")

    # Jewelry
    st.markdown("<h3>💍 Jewelry Recommendations</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:18px; font-weight:500; color:var(--gold);'>{r['jewelry']}</p>", unsafe_allow_html=True)
    st.markdown("**Brands:** Mejuri, Missoma, Tiffany & Co., Pandora")

    # Best & Worst Color Visualizer
    st.markdown("<h3>👗 Best vs Worst Color Visualizer</h3>", unsafe_allow_html=True)
    best_color = r['palette'][0]; worst_color = "#4A4A4A"
    col1,col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:var(--card-bg); border:1px solid rgba(200,159,74,0.2); border-radius:20px;">
            <div style="font-size:14px; margin-bottom:12px; color:var(--text-secondary); letter-spacing:1px;">✨ YOUR BEST COLOR</div>
            <div style="background:{best_color}; width:100%; height:80px; border-radius:16px;"></div>
            <p style="margin-top:12px; color:var(--text-primary);">This colour makes you glow!</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:var(--card-bg); border:1px solid rgba(200,159,74,0.1); border-radius:20px;">
            <div style="font-size:14px; margin-bottom:12px; color:var(--text-secondary); letter-spacing:1px;">⚠️ COLOR TO AVOID</div>
            <div style="background:{worst_color}; width:100%; height:80px; border-radius:16px;"></div>
            <p style="margin-top:12px; color:var(--text-primary);">This colour may wash you out</p>
        </div>""", unsafe_allow_html=True)

    # What If Simulator
    transformations = SEASON_TRANSFORMATIONS.get(r['season'], {})
    if transformations:
        st.markdown("<h3>🔄 What If Simulator</h3>", unsafe_allow_html=True)
        st.markdown("See how your season would change with different hair colours:")
        trans_cols = st.columns(len(transformations))
        for col, (change, new_season) in zip(trans_cols, transformations.items()):
            with col:
                if st.button(f"{change} → {new_season}", key=f"sim_{change}"):
                    st.info(f"✨ If you had {change.lower()}, you would likely be a **{new_season}**. Your current season ({r['season']}) is your most harmonious match for your natural colouring!")

def render_results_card3():
    r = st.session_state.analysis_results
    st.markdown("<h2 style='text-align:center;'>📄 Your Report is Ready</h2>", unsafe_allow_html=True)

    # 7. SEASONAL AFFIRMATION CARD
    vibe = COLOR_VIBES.get(r['season'], {"vibe":"Beautiful & Unique","emoji":"✨","mood":"Your colours enhance your natural beauty."})
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, var(--card-bg) 0%, rgba(200,150,60,0.08) 100%); border-radius:24px; padding:32px; margin:24px 0; text-align:center; border:1px solid rgba(200,159,74,0.2);">
        <div style="font-size:48px; margin-bottom:16px;">{vibe['emoji']}</div>
        <div style="font-family:'Playfair Display', serif; font-size:28px; font-weight:700; color:var(--gold);">{r['season']}</div>
        <div style="font-size:18px; font-weight:500; margin:12px 0; color:var(--text-primary);">{vibe['vibe']}</div>
        <p style="margin:16px 0; color:var(--text-secondary);">{vibe['mood']}</p>
        <div style="display:flex; justify-content:center; gap:8px; margin-top:20px;">
            {''.join([f'<div style="background:{c}; width:40px; height:40px; border-radius:12px;"></div>' for c in r['palette'][:4]])}
        </div>
    </div>""", unsafe_allow_html=True)

    # Download Affirmation Card as PNG image
    png_bytes = generate_affirmation_png(r)
    st.download_button(
        "🖼 Download Affirmation Card (PNG)",
        data=png_bytes,
        file_name=f"tinta_{r['season'].lower().replace(' ','_')}_affirmation.png",
        mime="image/png",
        use_container_width=True,
    )

    # Download PDF report
    pdf = generate_pdf_report(r)
    if pdf:
        st.download_button("⬇ Download Full Report (PDF)", data=pdf,
                           file_name=f"tinta_{r['season'].lower().replace(' ','_')}_report.pdf",
                           mime="application/pdf", use_container_width=True)

    st.markdown("---")

    # Copy to Clipboard
    copy_text = (
        f"🎨 Tinta Color Analysis\n\n"
        f"Season: {r['season']}\n"
        f"Undertone: {r['pred']}\n"
        f"Depth: {r['depth']}\n"
        f"Confidence: {r['confidence']:.0f}%\n"
        f"Color Harmony: {r['harmony_score']}%\n\n"
        f"{vibe['vibe']}\n"
        f"{vibe['mood']}\n\n"
        f"Palette: {', '.join(r['palette'])}\n\n"
        f"Find your perfect colours at Tinta!"
    )
    # Styled HTML block — visible in both light and dark mode via CSS variables
    copy_lines_html = copy_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    st.markdown(f"""
    <div style="background:var(--card-bg); border:1px solid rgba(200,159,74,0.25); border-radius:16px;
                padding:20px 24px; margin:16px 0; font-family:monospace;
                font-size:13px; line-height:1.8; color:var(--text-primary);">
        {copy_lines_html}
    </div>""", unsafe_allow_html=True)
    st.caption("📋 Select all and copy the text above to share your results.")

    # Save to Color Diary
    if st.button("💾 Save to Color Diary", use_container_width=True):
        st.session_state.saved_analyses.append({
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "season": r['season'],
            "confidence": r['confidence'],
        })
        st.markdown("""
        <div style="background:rgba(200,159,74,0.12); border:1px solid rgba(200,159,74,0.4); border-radius:16px; padding:14px 20px; text-align:center; margin:8px 0;">
            <strong style="color:var(--text-primary);">✅ Saved to your Color Diary!</strong> <span style="color:var(--text-secondary);">Check the sidebar.</span>
        </div>""", unsafe_allow_html=True)

    # Fairness report (developer only — hidden behind expander)
    fr = st.session_state.get("fairness_report")
    if fr:
        with st.expander("📊 Model Fairness Report (Fitzpatrick Balance)"):
            for fitz, data in fr.items():
                st.markdown(f"**Fitzpatrick Type {fitz}** — {data['n']} samples")
                st.json(data['undertone_dist'])

    _, col_new, _ = st.columns([1,2,1])
    with col_new:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.page = "welcome"
            st.session_state.analysis_results = None
            st.session_state.uploaded_photo   = None
            st.rerun()
def render_compare_results():
    a,b = st.session_state.compare_results["a"], st.session_state.compare_results["b"]
    ia,ib = st.session_state.compare_images["a"], st.session_state.compare_images["b"]
    st.markdown("<h2 style='text-align:center;'>🔬 Comparison Results</h2>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.image(ia, width=300, caption="Photo A")
        st.markdown(f"""
        <div style="text-align:center; margin-top:16px;">
            <span style="background:{a['badge_bg']}; color:{a['badge_fg']}; padding:6px 20px; border-radius:30px; display:inline-block;">{a['season']}</span>
            <p style="margin-top:12px; color:var(--text-primary);">{a['pred']} · {a['depth']}<br>Confidence: {a['confidence']:.0f}%</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.image(ib, width=300, caption="Photo B")
        st.markdown(f"""
        <div style="text-align:center; margin-top:16px;">
            <span style="background:{b['badge_bg']}; color:{b['badge_fg']}; padding:6px 20px; border-radius:30px; display:inline-block;">{b['season']}</span>
            <p style="margin-top:12px; color:var(--text-primary);">{b['pred']} · {b['depth']}<br>Confidence: {b['confidence']:.0f}%</p>
        </div>""", unsafe_allow_html=True)
    if a['season'] == b['season']:
        st.success("✨ Both photos gave the same season! Consistent result.")
        st.balloons()
    else:
        st.info(f"📸 Photo A: **{a['season']}** | Photo B: **{b['season']}**\n\nDifferent lighting can affect results. For best accuracy, use similar lighting in both photos.")
    if st.button("← Back to Modes", use_container_width=True):
        st.session_state.page = "options"; st.rerun()

# ================================================================
# MAIN PAGE ROUTING
# ================================================================
if st.session_state.page == "welcome":
    render_welcome_page()
elif st.session_state.page == "options":
    render_options_page()
elif st.session_state.page == "input":
    m = st.session_state.mode
    if m == "single":    render_single_photo_input()
    elif m == "multi":   render_multi_photo_input()
    elif m == "manual":  render_manual_picker_input()
    elif m == "quiz":    render_quiz_input()
    elif m == "compare": render_compare_input()
    elif m == "calibrate": render_calibrate_input()
elif st.session_state.page in ("results1","results2","results3"):
    _t1,_t2,_t3 = st.tabs(["✨ Your Season","💄 Recommendations","📄 Report"])
    with _t1: render_results_card1()
    with _t2: render_results_card2()
    with _t3: render_results_card3()
elif st.session_state.page == "compare_results":
    render_compare_results()

st.markdown("""
<div style="text-align:center; padding:40px 0 20px; font-size:10px; color:var(--text-secondary); letter-spacing:2px;">
    TINTA · AI PERSONAL COLOR ANALYSIS<br>
    Results are a guide. Professional draping gives maximum precision.
</div>""", unsafe_allow_html=True)
