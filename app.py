from __future__ import annotations

from io import BytesIO
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from random import Random
from time import time_ns

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageStat

from datos import EXERCISE_ROUTINES, FOOD_DATABASE, RECIPE_POOL, WEEK_DAYS
from modelo_ai import model_card_text, predict_ai_risk


st.set_page_config(
    page_title="ç³–å°¿ç—…è‚¾ç—…ç…§æŠ¤åŠ©æ‰‹",
    page_icon="ðŸ’š",
    layout="wide",
    initial_sidebar_state="collapsed",
)


STATUS_META = {
    "eat": {
        "label": "âœ… å¯ä»¥åƒ",
        "color": "#008f5f",
        "bg": "#e9f8f0",
        "border": "rgba(0, 143, 95, 0.40)",
    },
    "moderate": {
        "label": "âš ï¸ é€‚é‡åƒ",
        "color": "#a46a00",
        "bg": "#fff8e6",
        "border": "rgba(164, 106, 0, 0.36)",
    },
    "avoid": {
        "label": "âŒ é¿å…",
        "color": "#c62845",
        "bg": "#fff0f3",
        "border": "rgba(198, 40, 69, 0.36)",
    },
}


ASSET_DIR = Path(__file__).parent / "assets"
RECIPE_ASSET_DIR = ASSET_DIR / "recipes"
MEAL_IMAGE = {
    "æ—©é¤": ASSET_DIR / "breakfast.png",
    "åˆé¤": ASSET_DIR / "lunch.png",
    "æ™šé¤": ASSET_DIR / "dinner.png",
}


def setup_state() -> None:
    if "glucose_records" not in st.session_state:
        st.session_state.glucose_records = []
    if "medications" not in st.session_state:
        st.session_state.medications = []
    if "med_log" not in st.session_state:
        st.session_state.med_log = {}
    if "dialysis_days" not in st.session_state:
        st.session_state.dialysis_days = ["å‘¨ä¸‰"]
    if "face_baseline" not in st.session_state:
        st.session_state.face_baseline = None
    if "face_history" not in st.session_state:
        st.session_state.face_history = []
    if "hospital_phone" not in st.session_state:
        st.session_state.hospital_phone = ""
    if "face_photo_source" not in st.session_state:
        st.session_state.face_photo_source = "camera"
    if "current_module" not in st.session_state:
        st.session_state.current_module = "首页"


def inject_style() -> None:
    st.html(
        """
        <style>
        :root {
            --bg: #f7fafc;
            --primary: #008f5f;
            --secondary: #ffffff;
            --text: #17202a;
            --muted: #52616f;
            --danger: #c62845;
            --warning: #a46a00;
            --line: #d8e2ea;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--bg);
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: #eef7f1;
            border-right: 1px solid #cfe3d8;
        }

        [data-testid="stSidebar"] * {
            font-size: 20px !important;
        }

        .stSelectbox label, .stTextInput label, .stNumberInput label,
        .stDateInput label, .stTimeInput label, .stTextArea label,
        .stMultiSelect label {
            color: var(--text) !important;
            font-size: 22px !important;
            font-weight: 700 !important;
        }

        .stButton > button, .stFormSubmitButton > button {
            min-height: 56px;
            border-radius: 8px;
            border: 1px solid rgba(0, 143, 95, 0.45);
            background: #ffffff;
            color: var(--text);
            font-size: 20px;
            font-weight: 800;
            box-shadow: 0 1px 2px rgba(23, 32, 42, 0.08);
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        input, textarea, [data-baseweb="select"] * {
            font-size: 20px !important;
        }

        [data-testid="stImage"] img {
            border-radius: 8px;
            border: 1px solid var(--line);
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.08);
            margin-bottom: 8px;
        }

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1220px;
        }

        .main-title {
            font-size: 42px;
            line-height: 1.2;
            font-weight: 900;
            color: var(--primary);
            margin-bottom: 8px;
        }

        .subtitle {
            font-size: 22px;
            color: var(--muted);
            margin-bottom: 20px;
        }

        .notice {
            font-size: 20px;
            line-height: 1.6;
            border: 1px solid rgba(164, 106, 0, 0.28);
            background: #fff8e6;
            color: #533900;
            border-radius: 8px;
            padding: 16px 18px;
            margin: 12px 0 20px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }

        .lobby-hero {
            border-radius: 8px;
            padding: 26px;
            background: linear-gradient(135deg, #e9f8f0 0%, #ffffff 55%, #eef5ff 100%);
            border: 1px solid #cfe3d8;
            box-shadow: 0 4px 18px rgba(23, 32, 42, 0.08);
            margin-bottom: 18px;
        }

        .lobby-title {
            font-size: 40px;
            font-weight: 900;
            color: #008f5f;
            line-height: 1.18;
            margin-bottom: 8px;
        }

        .lobby-subtitle {
            font-size: 24px;
            color: #34495e;
            line-height: 1.5;
        }

        .quick-card {
            min-height: 190px;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 3px 12px rgba(23, 32, 42, 0.08);
        }

        .quick-card.primary {
            border-color: rgba(0, 143, 95, 0.32);
            background: #f3fcf7;
        }

        .quick-title {
            font-size: 28px;
            font-weight: 900;
            color: #102030;
            margin-bottom: 6px;
        }

        .quick-desc {
            font-size: 21px;
            color: var(--muted);
            line-height: 1.45;
        }

        .action-card {
            min-height: 220px;
            background: #ffffff;
            border: 1px solid #d8e2ea;
            border-radius: 8px;
            padding: 22px 20px;
            box-shadow: 0 4px 16px rgba(23, 32, 42, 0.08);
            text-align: center;
            margin-bottom: 10px;
        }

        .action-card.primary {
            background: #f3fcf7;
            border-color: rgba(0, 143, 95, 0.35);
        }

        .action-icon {
            font-size: 54px;
            line-height: 1;
            margin-bottom: 12px;
        }

        .action-title {
            font-size: 31px;
            line-height: 1.2;
            font-weight: 900;
            color: #102030;
            margin-bottom: 10px;
        }

        .action-hint {
            font-size: 20px;
            line-height: 1.45;
            color: #52616f;
        }

        .section-tip {
            font-size: 20px;
            line-height: 1.5;
            color: #52616f;
            margin: 2px 0 14px;
        }

        .module-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin: 10px 0 18px;
        }

        .module-action-card {
            min-height: 150px;
            background: #ffffff;
            border: 1px solid #d8e2ea;
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 3px 12px rgba(23, 32, 42, 0.06);
        }

        .module-action-card.primary {
            background: #f3fcf7;
            border-color: rgba(0, 143, 95, 0.35);
        }

        .module-action-card.alert {
            background: #fff5f7;
            border-color: rgba(198, 40, 69, 0.30);
        }

        .module-action-title {
            font-size: 26px;
            line-height: 1.2;
            font-weight: 900;
            color: #102030;
            margin: 8px 0 6px;
        }

        .module-action-desc {
            font-size: 19px;
            line-height: 1.45;
            color: #52616f;
        }

        .calendar-strip {
            display: grid;
            grid-template-columns: repeat(7, minmax(92px, 1fr));
            gap: 10px;
            margin: 12px 0 18px;
        }

        .calendar-day {
            min-height: 112px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #ffffff;
            padding: 12px;
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.05);
        }

        .calendar-day.today {
            border: 2px solid #008f5f;
            background: #e9f8f0;
        }

        .calendar-day.dialysis {
            border-color: rgba(198, 40, 69, 0.35);
            background: #fff0f3;
        }

        .calendar-name {
            font-size: 20px;
            font-weight: 900;
            color: #102030;
        }

        .calendar-date {
            font-size: 18px;
            color: var(--muted);
            margin: 4px 0;
        }

        .calendar-note {
            font-size: 18px;
            font-weight: 800;
            color: #008f5f;
        }

        .todo-item {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            border: 1px solid var(--line);
            background: #ffffff;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.05);
        }

        .todo-icon {
            font-size: 32px;
            line-height: 1;
            min-width: 38px;
        }

        .todo-title {
            font-size: 22px;
            font-weight: 900;
            color: #102030;
            margin-bottom: 2px;
        }

        .todo-desc {
            font-size: 19px;
            color: var(--muted);
            line-height: 1.45;
        }

        .card {
            background: var(--secondary);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.06);
        }

        .card-title {
            font-size: 26px;
            font-weight: 900;
            margin-bottom: 10px;
            color: #102030;
        }

        .big-icon {
            font-size: 42px;
            line-height: 1;
            margin-bottom: 8px;
        }

        .big-text {
            font-size: 22px;
            line-height: 1.65;
            color: var(--text);
        }

        .muted {
            color: var(--muted);
        }

        .pill {
            display: inline-flex;
            align-items: center;
            min-height: 38px;
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 20px;
            font-weight: 900;
            margin-bottom: 12px;
        }

        .day-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(116px, 1fr));
            gap: 12px;
            margin: 18px 0;
        }

        .day-box {
            min-height: 150px;
            border-radius: 8px;
            padding: 14px;
            background: var(--secondary);
            border: 1px solid var(--line);
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.06);
        }

        .day-box.safe {
            border-color: rgba(0, 143, 95, 0.34);
            background: #eefaf4;
        }

        .day-box.stop {
            border-color: rgba(198, 40, 69, 0.32);
            background: #fff0f3;
        }

        .day-name {
            font-size: 24px;
            font-weight: 900;
            margin-bottom: 12px;
        }

        .day-action {
            font-size: 20px;
            line-height: 1.45;
        }

        .meal-card {
            background: var(--secondary);
            border: 1px solid rgba(0, 143, 95, 0.24);
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(23, 32, 42, 0.06);
        }

        .meal-head {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }

        .meal-time {
            color: var(--primary);
            font-size: 24px;
            font-weight: 900;
        }

        .meal-name {
            color: #102030;
            font-size: 28px;
            font-weight: 900;
        }

        .nutrient-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }

        .nutrient-chip {
            border: 1px solid rgba(0, 143, 95, 0.30);
            background: #e9f8f0;
            color: #006b47;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 18px;
            font-weight: 800;
        }

        .simple-list {
            margin: 8px 0 0 22px;
            padding: 0;
        }

        .simple-list li {
            font-size: 21px;
            line-height: 1.55;
            margin-bottom: 4px;
        }

        .alert-red {
            border: 2px solid rgba(198, 40, 69, 0.52);
            background: #fff0f3;
            color: #8a1028;
            border-radius: 8px;
            padding: 18px;
            font-size: 24px;
            font-weight: 900;
            margin: 12px 0;
        }

        .alert-green {
            border: 2px solid rgba(0, 143, 95, 0.38);
            background: #e9f8f0;
            color: #005a3c;
            border-radius: 8px;
            padding: 18px;
            font-size: 24px;
            font-weight: 900;
            margin: 12px 0;
        }

        @media (max-width: 900px) {
            .day-grid {
                grid-template-columns: repeat(2, minmax(140px, 1fr));
            }

            .calendar-strip {
                grid-template-columns: repeat(2, minmax(140px, 1fr));
            }

            .quick-card {
                min-height: 140px;
            }

            .action-card {
                min-height: 200px;
            }

            .main-title {
                font-size: 34px;
            }

            .lobby-title {
                font-size: 34px;
            }
        }
        </style>
        """
    )


def page_header(title: str, subtitle: str) -> None:
    if st.session_state.get("current_module") != "é¦–é¡µ":
        if st.button("â† è¿”å›žé¦–é¡µ", key=f"back_{title}", use_container_width=True):
            go_to_module("é¦–é¡µ")
    st.html(
        f"""
        <div class="main-title">{escape(title)}</div>
        <div class="subtitle">{escape(subtitle)}</div>
        <div class="notice">âš•ï¸ æœ¬åº”ç”¨åªç”¨äºŽæ—¥å¸¸è®°å½•å’Œæé†’ï¼Œä¸èƒ½æ›¿ä»£åŒ»ç”Ÿã€æŠ¤å£«æˆ–è¥å…»å¸ˆçš„å»ºè®®ã€‚è‹¥å‡ºçŽ°èƒ¸ç—›ã€ä¸¥é‡ä½Žè¡€ç³–ã€å‘¼å¸å›°éš¾æˆ–é€æžä¸é€‚ï¼Œè¯·ç«‹å³è”ç³»åŒ»ç–—äººå‘˜ã€‚</div>
        """
    )


def section_title(text: str) -> None:
    st.html(f'<div class="card-title" style="margin-top: 18px;">{escape(text)}</div>')


def info_card(title: str, body: str, icon: str = "â„¹ï¸") -> None:
    st.html(
        f"""
        <div class="card">
            <div class="big-icon">{escape(icon)}</div>
            <div class="card-title">{escape(title)}</div>
            <div class="big-text">{body}</div>
        </div>
        """
    )


def render_food_card(food: dict) -> None:
    meta = STATUS_META[food["status"]]
    st.html(
        f"""
        <div class="card" style="border-color:{meta["border"]}; background:{meta["bg"]};">
            <div class="pill" style="color:{meta["color"]}; border:1px solid {meta["border"]}; background:#ffffff;">
                {meta["label"]}
            </div>
            <div class="card-title">{escape(food["name"])}</div>
            <div class="big-text"><b>å»ºè®®é‡ï¼š</b>{escape(food["portion"])}</div>
            <div class="big-text"><b>åŽŸå› ï¼š</b>{escape(food["reason"])}</div>
            <div class="big-text muted"><b>æé†’ï¼š</b>{escape(food["tips"])}</div>
        </div>
        """
    )


def measured_recipe_items(meal: dict) -> list[str]:
    name = meal["name"]
    ingredients_text = " ".join(meal["ingredients"])
    items = []

    if "ç²¥" in name:
        items.append("ç™½ç±³ï¼šç”Ÿç±³25å…‹ï¼Œç…®æˆ1å°ç¢—ç²¥ï¼›æ¸…æ°´300-350æ¯«å‡ï¼Œæ±¤æ°´éœ€è®¡å…¥æ¯æ—¥é¥®æ°´é‡ã€‚")
    elif "ç±³é¥­" in name or "é¥­" in name or "ç›–é¥­" in name or "é¥­ç›’" in name:
        items.append("ç±³é¥­ï¼šç†Ÿç±³é¥­80-100å…‹ï¼Œçº¦å°åŠç¢—ï¼›è¡€ç³–é«˜æ—¶å‡åˆ°60-80å…‹ã€‚")
    elif "é¢" in name or "ç±³ç²‰" in name or "ç²‰ä¸" in name or "æ±¤ç²‰" in name:
        items.append("é¢/ç±³ç²‰/ç²‰ä¸ï¼šå¹²é‡30-40å…‹ï¼Œç…®ç†ŸåŽçº¦åŠç¢—ï¼›æ±¤ä¸è¦å¤šå–ã€‚")
    elif "é¦’å¤´" in name:
        items.append("é¦’å¤´ï¼šåŠä¸ªå°é¦’å¤´ï¼Œçº¦30-40å…‹ã€‚")
    elif "é¥º" in name or "é¦„é¥¨" in name:
        items.append("é¥ºå­/é¦„é¥¨çš®ï¼š4-6ä¸ªå°ä»½ï¼Œæ€»é‡çº¦50-70å…‹ï¼›åŒé¤ä¸å†åŠ ç±³é¥­ã€‚")
    elif "é¥¼" in name:
        items.append("é¢ç²‰ï¼š25å…‹ï¼›æ¸…æ°´30-40æ¯«å‡ï¼›åšæˆ1å¼ å°é¥¼ã€‚")
    elif "åå¸" in name:
        items.append("æ— ç³–åå¸ï¼šåŠç‰‡åˆ°1ç‰‡ï¼Œçº¦20-30å…‹ã€‚")
    else:
        items.append("ä¸»é£Ÿï¼šå¦‚æœ¬é¤å«é¥­ã€é¢æˆ–ç²¥ï¼ŒæŽ§åˆ¶åœ¨å°åŠç¢—ï¼›å¦‚æ²¡æœ‰ä¸»é£Ÿï¼Œå¯æŒ‰åŒ»å˜±åŠ å°åŠç¢—ç±³é¥­ã€‚")

    if "é±¼" in ingredients_text or "é±¼" in name:
        items.append("ç™½è‚‰é±¼ï¼š60-80å…‹ï¼Œçº¦1ä¸ªæŽŒå¿ƒå¤§å°ï¼Œæ¸…è’¸æˆ–æ°´ç…®ã€‚")
    if "é¸¡" in ingredients_text or "é¸¡" in name:
        items.append("åŽ»çš®é¸¡èƒ¸è‚‰ï¼š60-80å…‹ï¼Œçº¦1ä¸ªæŽŒå¿ƒå¤§å°ï¼›æ—©é¤å¯ç”¨30-50å…‹ã€‚")
    if "è›‹æ¸…" in ingredients_text or "è›‹æ¸…" in name:
        items.append("é¸¡è›‹æ¸…ï¼š1ä¸ªï¼Œçº¦30å…‹ï¼›éœ€è¦æ›´å¤šè›‹ç™½æ—¶æŒ‰åŒ»å˜±å¯ç”¨2ä¸ªã€‚")
    if "è±†è…" in ingredients_text or "è±†è…" in name:
        items.append("è±†è…ï¼š40-60å…‹ï¼Œå°å—ï¼›è¡€ç£·é«˜æ—¶å‡å°‘æˆ–æ”¹ç”¨è›‹æ¸…ã€‚")
    if "ç‰›è‚‰" in ingredients_text or "ç‰›è‚‰" in name:
        items.append("ç˜¦ç‰›è‚‰ï¼š40-50å…‹ï¼Œå°‘é‡å³å¯ï¼Œä¸å»ºè®®å¤©å¤©åƒã€‚")
    if "è™¾ä»" in ingredients_text or "è™¾ä»" in name:
        items.append("è™¾ä»ï¼š40-50å…‹ï¼›å°¿é…¸é«˜æˆ–åŒ»ç”Ÿé™åˆ¶æµ·é²œæ—¶ä¸è¦ç”¨ã€‚")

    items.append("è”¬èœï¼šç†Ÿèœ80-120å…‹ï¼Œçº¦åŠç¢—ï¼›ç»¿å¶èœå…ˆç”¨500æ¯«å‡æ¸…æ°´ç„¯30-60ç§’åŽå€’æŽ‰æ°´ã€‚")
    items.append("é£Ÿç”¨æ²¹ï¼šæ¯é¤æœ€å¤š1èŒ¶åŒ™ï¼Œçº¦5æ¯«å‡ï¼›æ—©é¤å¯ç”¨0-2æ¯«å‡æˆ–ä¸æ”¾æ²¹ã€‚")
    items.append("ç›ï¼šæœ€å¥½ä¸åŠ ï¼›å¦‚æžœå¿…é¡»åŠ ï¼Œå…¨é¤æœ€å¤š1/8èŒ¶åŒ™ï¼Œçº¦0.5-0.7å…‹ã€‚")
    items.append("é…±æ²¹ï¼šå»ºè®®0æ¯«å‡ï¼›å¦‚åŒ»ç”Ÿå…è®¸ï¼Œæœ€å¤š1/4èŒ¶åŒ™ï¼Œçº¦1æ¯«å‡ï¼Œä¸èƒ½å†é¢å¤–åŠ ç›ã€‚")
    items.append("è°ƒå‘³ï¼šå§œ2-3ç‰‡ï¼Œè‘±èŠ±3å…‹ï¼Œé†‹1èŒ¶åŒ™çº¦5æ¯«å‡ï¼Œæˆ–æŸ æª¬æ±1èŒ¶åŒ™çº¦5æ¯«å‡ã€‚")
    return items


def detailed_recipe_steps(meal: dict) -> list[str]:
    name = meal["name"]
    steps = [
        "æ´—æ‰‹20ç§’ï¼Œå‡†å¤‡å¹²å‡€ç §æ¿ã€åˆ€ã€é”…ã€é‡å‹ºå’Œå°ç¢—ã€‚",
        "å…ˆæŒ‰â€œè¯¦ç»†ç”¨é‡â€ç§°å¥½é£Ÿæï¼šä¸»é£Ÿå°ä»½ã€è›‹ç™½1æŽŒå¿ƒæˆ–æŒ‡å®šå…‹æ•°ã€è”¬èœåŠç¢—ã€‚",
        "è”¬èœç”¨æ¸…æ°´æ´—å‡€ï¼›ç»¿å¶èœç”¨500æ¯«å‡å¼€æ°´ç„¯30-60ç§’ï¼Œæžå‡ºåŽå€’æŽ‰ç„¯èœæ°´ã€‚",
        "é”…ä¸­æœ€å¤šæ”¾1èŒ¶åŒ™æ²¹ï¼Œçº¦5æ¯«å‡ï¼›æ—©é¤æˆ–ç²¥ç±»å¯ä»¥ä¸æ”¾æ²¹ã€‚",
    ]

    if "é±¼" in name:
        steps.append("é±¼è‚‰60-80å…‹åŠ å§œ2-3ç‰‡ï¼Œè’¸8-10åˆ†é’Ÿæˆ–ç…®åˆ°å®Œå…¨å˜ç™½ç†Ÿé€ã€‚")
    elif "é¸¡" in name:
        steps.append("é¸¡èƒ¸è‚‰60-80å…‹ç”¨æ¸…æ°´ç…®æˆ–è’¸10-15åˆ†é’Ÿï¼Œç†Ÿé€åŽåˆ‡ç‰‡æˆ–æ’•ä¸ã€‚")
    elif "è›‹æ¸…" in name:
        steps.append("é¸¡è›‹æ¸…1ä¸ªåŠ æ¸©æ°´30æ¯«å‡ï¼Œè’¸6-8åˆ†é’Ÿåˆ°å‡å›ºï¼›ä¸è¦åŠ å…¥è›‹é»„ã€‚")
    elif "è±†è…" in name:
        steps.append("è±†è…40-60å…‹åˆ‡å°å—ï¼Œè’¸æˆ–ç…®3-5åˆ†é’Ÿï¼›ä¸è¦æ²¹ç‚¸ã€‚")
    else:
        steps.append("è›‹ç™½ç±»é£ŸææŒ‰é£Ÿè°±ç…®ç†Ÿæˆ–è’¸ç†Ÿï¼Œä¸ä½¿ç”¨è…Œåˆ¶å“ã€å’¸é±¼ã€é¦™è‚ æˆ–é«˜ç›é…±æ–™ã€‚")

    if "ç²¥" in name:
        steps.append("ç”Ÿç±³25å…‹åŠ æ¸…æ°´300-350æ¯«å‡ç…®æˆ1å°ç¢—ç²¥ï¼›ä¸è¦åŠ ç³–ã€‚")
    elif "é¥­" in name:
        steps.append("ç†Ÿç±³é¥­ç§°80-100å…‹ï¼Œæ”¾å…¥å°ç¢—ï¼›å…ˆåƒèœå’Œè›‹ç™½ï¼Œå†åƒç±³é¥­ã€‚")
    elif "é¢" in name or "ç±³ç²‰" in name or "ç²‰ä¸" in name:
        steps.append("å¹²é¢/ç±³ç²‰/ç²‰ä¸30-40å…‹ç…®ç†ŸåŽæ²¥æ°´ï¼›æ±¤æ±æœ€å¤šå–å‡ å£ï¼Œä¸è¦å–å®Œã€‚")
    elif "é¥º" in name or "é¦„é¥¨" in name:
        steps.append("é¥ºå­æˆ–é¦„é¥¨æŽ§åˆ¶4-6ä¸ªå°ä»½ï¼Œè’¸æˆ–æ¸…ç…®ï¼›ä¸è˜¸é…±æ²¹ã€‚")
    elif "é¥¼" in name:
        steps.append("é¢ç²‰25å…‹åŠ æ°´30-40æ¯«å‡è°ƒç³Šï¼Œç”¨ä¸ç²˜é”…å°‘æ²¹ç…Žæˆ1å¼ å°é¥¼ã€‚")

    steps.extend(meal["steps"])
    steps.extend(
        [
            "æœ€åŽè°ƒå‘³ï¼šä¼˜å…ˆç”¨è‘±ã€å§œã€é†‹æˆ–æŸ æª¬æ±ï¼›ç›æœ€å¤š1/8èŒ¶åŒ™ï¼Œé…±æ²¹å°½é‡ä¸ç”¨ã€‚",
            "è£…ç›˜åŽæ£€æŸ¥ä»½é‡ï¼šä¸»é£Ÿå°åŠç¢—ï¼Œè›‹ç™½1æŽŒå¿ƒï¼Œè”¬èœåŠç¢—ï¼›ä¸è¦å†åŠ ç”œé¥®æ–™ã€å’¸èœæˆ–æµ“æ±¤ã€‚",
            "å¦‚æžœå½“å¤©é€æžã€è¡€ç³–å¼‚å¸¸æˆ–åŒ»ç”Ÿæœ‰ç‰¹æ®Šé™åˆ¶ï¼Œä»¥åŒ»ç”Ÿå’Œè¥å…»å¸ˆçš„å»ºè®®ä¸ºå‡†ã€‚",
        ]
    )
    return steps


def render_recipe_card(meal: dict) -> None:
    specific_image = RECIPE_ASSET_DIR / f"{meal['id']}.png"
    image_path = specific_image if specific_image.exists() else MEAL_IMAGE.get(meal["time"])
    if image_path and image_path.exists():
        st.image(str(image_path), use_container_width=True)

    nutrients = "".join(
        f'<span class="nutrient-chip">{escape(item)}</span>' for item in meal["nutrients"]
    )
    ingredients = "".join(f"<li>{escape(item)}</li>" for item in measured_recipe_items(meal))
    detailed_steps = detailed_recipe_steps(meal)
    steps = "".join(f"<li>{escape(item)}</li>" for item in detailed_steps)
    st.html(
        f"""
        <div class="meal-card">
            <div class="meal-head">
                    <div class="big-icon" style="margin:0;">{escape(meal["icon"])}</div>
                <div>
                    <div class="meal-time">{escape(meal["time"])} Â· {escape(meal["style"])}</div>
                    <div class="meal-name">{escape(meal["name"])}</div>
                </div>
            </div>
            <div class="big-text"><b>å»ºè®®ä»½é‡ï¼š</b>{escape(meal["portion"])}</div>
            <div class="nutrient-row">{nutrients}</div>
            <div class="big-text"><b>è¯¦ç»†ç”¨é‡ï¼š</b></div>
            <ul class="simple-list">{ingredients}</ul>
            <div class="big-text" style="margin-top:10px;"><b>è¯¦ç»†åšæ³•ï¼š</b></div>
            <ol class="simple-list">{steps}</ol>
            <div class="notice" style="margin-bottom:0;"><b>è‚¾ç—…æé†’ï¼š</b>{escape(meal["renal_note"])}</div>
        </div>
        """
    )


def week_start_for(day: date) -> date:
    return day - timedelta(days=day.weekday())


def recipes_for_time(meal_time: str) -> list[dict]:
    return [recipe for recipe in RECIPE_POOL if recipe["time"] == meal_time]


def pick_recipes_for_week(week_start: date, meal_time: str) -> list[dict]:
    candidates = recipes_for_time(meal_time)
    ordered = candidates[:]
    Random(20260615 + sum(ord(char) for char in meal_time)).shuffle(ordered)

    first_known_monday = date(2020, 1, 6)
    week_index = (week_start - first_known_monday).days // 7
    start = (week_index * 7) % len(ordered)
    return [ordered[(start + offset) % len(ordered)] for offset in range(7)]


def build_generated_meal_plan(reference_day: date) -> list[dict]:
    week_start = week_start_for(reference_day)
    breakfast = pick_recipes_for_week(week_start, "æ—©é¤")
    lunch = pick_recipes_for_week(week_start, "åˆé¤")
    dinner = pick_recipes_for_week(week_start, "æ™šé¤")

    weekly_plan = []
    for index, day_name in enumerate(WEEK_DAYS):
        plan_date = week_start + timedelta(days=index)
        weekly_plan.append(
            {
                "day": day_name,
                "date": plan_date,
                "theme": "è‡ªåŠ¨ç”Ÿæˆå‡è¡¡é¤",
                "meals": [breakfast[index], lunch[index], dinner[index]],
            }
        )
    return weekly_plan


def render_meal_plan() -> None:
    section_title("è‡ªåŠ¨ç”Ÿæˆä¸€å‘¨ä¸‰é¤")
    st.html(
        """
        <div class="notice">
        ðŸ½ï¸ ç³»ç»Ÿä¼šä»Ž50ä¸ªé£Ÿè°±ä¸­ç”Ÿæˆæœ¬å‘¨ä¸‰é¤ã€‚æ¯å‘¨ä¼šè‡ªåŠ¨æ¢ä¸€ç»„ï¼Œå¹¶å°½é‡é¿å¼€ä¸Šä¸€å‘¨å·²ç»ç”¨è¿‡çš„é£Ÿè°±ã€‚é‡ç‚¹æ˜¯ä¼˜è´¨è›‹ç™½ã€å°‘é‡ä¸»é£Ÿã€ä½Žç›ã€ä½Žé’¾ã€ä½Žç£·å’Œç¨³å®šè¡€ç³–ã€‚
        </div>
        """
    )

    reference_day = st.date_input("ðŸ“… é€‰æ‹©æœ¬å‘¨ä»»æ„ä¸€å¤©", value=date.today())
    week_start = week_start_for(reference_day)
    iso = week_start.isocalendar()
    weekly_plan = build_generated_meal_plan(reference_day)
    selected_day = st.selectbox(
        "ðŸ“… é€‰æ‹©ä¸€å¤©æŸ¥çœ‹ä¸‰é¤",
        [f"{item['day']} {item['date'].strftime('%m-%d')}" for item in weekly_plan],
    )
    day_plan = weekly_plan[
        [f"{item['day']} {item['date'].strftime('%m-%d')}" for item in weekly_plan].index(selected_day)
    ]

    st.html(
        f"""
        <div class="card" style="border-color:rgba(0,143,95,0.35);">
            <div class="card-title">ç¬¬ {iso.week} å‘¨ Â· {week_start.strftime("%Y-%m-%d")} å¼€å§‹</div>
            <div class="big-text">{escape(day_plan["day"])} çš„æ—©é¤ã€åˆé¤å’Œæ™šé¤å¦‚ä¸‹ã€‚æ¯é¤éƒ½å°½é‡ä½¿ç”¨ä¸­å¼åšæ³•ï¼Œå¹¶æŽ§åˆ¶ç›ã€ç³–ã€é’¾å’Œç£·ã€‚</div>
        </div>
        """
    )

    for meal in day_plan["meals"]:
        render_recipe_card(meal)

    show_week = st.checkbox("ðŸ—“ï¸ æ˜¾ç¤ºä¸€å‘¨æ€»è§ˆ")
    if show_week:
        overview_rows = []
        for day in weekly_plan:
            overview_rows.append(
                {
                    "æ—¥æœŸ": day["day"],
                    "æ—¥æœŸæ•°å­—": day["date"].strftime("%m-%d"),
                    "æ—©é¤": day["meals"][0]["name"],
                    "åˆé¤": day["meals"][1]["name"],
                    "æ™šé¤": day["meals"][2]["name"],
                }
            )
        st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)


def food_matches(food: dict, query: str) -> bool:
    if not query:
        return True
    q = query.strip().lower()
    target = " ".join([food["name"], *food["aliases"]]).lower()
    return q in target


def diet_module() -> None:
    page_header("é¥®é£ŸåŠ©æ‰‹", "æŸ¥çœ‹ä¸€å‘¨ä¸‰é¤é£Ÿè°±ï¼Œä¹Ÿå¯ä»¥æœç´¢å¸¸è§ä¸­é¤é£Ÿç‰©æ˜¯å¦é€‚åˆã€‚")

    st.html(
        """
        <div class="grid">
            <div class="card"><div class="big-icon">ðŸŒ</div><div class="big-text"><b>ä½Žé’¾ï¼š</b>é¿å…é¦™è•‰ã€ç•ªèŒ„ã€åœŸè±†ã€‚</div></div>
            <div class="card"><div class="big-icon">ðŸ¥›</div><div class="big-text"><b>ä½Žç£·ï¼š</b>å°‘å¥¶åˆ¶å“ï¼Œé¿å…åšæžœã€‚</div></div>
            <div class="card"><div class="big-icon">ðŸ§‚</div><div class="big-text"><b>ä½Žé’ ï¼š</b>é…±æ²¹ã€å’¸èœã€è…Œåˆ¶å“è¦å°‘ã€‚</div></div>
            <div class="card"><div class="big-icon">ðŸ©¸</div><div class="big-text"><b>æŽ§ç³–ï¼š</b>ä¸åŠ ç³–ï¼Œç™½ç±³é¥­è¦é™é‡ã€‚</div></div>
        </div>
        """
    )

    render_meal_plan()

    section_title("é£Ÿç‰©æœç´¢")
    query = st.text_input("ðŸ”Ž è¾“å…¥é£Ÿç‰©åç§°", placeholder="ä¾‹å¦‚ï¼šç±³é¥­ã€è±†è…ã€é…±æ²¹ã€é¦™è•‰ã€é’èœ")
    results = [food for food in FOOD_DATABASE if food_matches(food, query)]

    if not results:
        info_card("æ²¡æœ‰æ‰¾åˆ°", "è¯·æ¢ä¸€ä¸ªå¸¸è§åç§°æœç´¢ï¼Œæˆ–å’¨è¯¢åŒ»ç”Ÿ/è¥å…»å¸ˆã€‚", "ðŸ”Ž")
        return

    section_title(f"æ‰¾åˆ° {len(results)} ä¸ªç»“æžœ")
    for food in results:
        render_food_card(food)


def exercise_module() -> None:
    page_header("è¿åŠ¨è®¡åˆ’", "é€‰æ‹©é€æžæ—¥ï¼Œè‡ªåŠ¨ç”Ÿæˆæ¯å‘¨å®‰å…¨æ´»åŠ¨å®‰æŽ’ã€‚é€æžå½“å¤©ä¸å®‰æŽ’è¿åŠ¨ã€‚")

    dialysis_days = st.multiselect(
        "ðŸ©º è¯·é€‰æ‹©æ¯å‘¨é€æžæ—¥",
        WEEK_DAYS,
        default=st.session_state.dialysis_days,
    )
    st.session_state.dialysis_days = dialysis_days

    boxes = []
    for index, day_name in enumerate(WEEK_DAYS):
        is_dialysis = day_name in dialysis_days
        if is_dialysis:
            class_name = "day-box stop"
            icon = "ðŸ›‘"
            action = "é€æžæ—¥<br><b>ä»Šå¤©ä¸è¿åŠ¨</b><br>æ³¨æ„ä¼‘æ¯"
        else:
            routine = EXERCISE_ROUTINES[index % len(EXERCISE_ROUTINES)]
            class_name = "day-box safe"
            icon = routine["icon"]
            action = f'{escape(routine["name"])}<br><b>{escape(routine["duration"])}</b><br>{escape(routine["intensity"])}'

        boxes.append(
            f"""
            <div class="{class_name}">
                <div class="day-name">{escape(day_name)}</div>
                <div class="big-icon">{icon}</div>
                <div class="day-action">{action}</div>
            </div>
            """
        )

    st.html(f'<div class="day-grid">{"".join(boxes)}</div>')

    section_title("å®‰å…¨è¿åŠ¨")
    cols = st.columns(2)
    for idx, routine in enumerate(EXERCISE_ROUTINES):
        steps = "".join(f"<li>{escape(step)}</li>" for step in routine["steps"])
        with cols[idx % 2]:
            st.html(
                f"""
                <div class="card">
                    <div class="big-icon">{routine["icon"]}</div>
                    <div class="card-title">{escape(routine["name"])}</div>
                    <div class="big-text"><b>æ—¶é—´ï¼š</b>{escape(routine["duration"])}</div>
                    <div class="big-text"><b>å¼ºåº¦ï¼š</b>{escape(routine["intensity"])}</div>
                    <div class="big-text"><ul>{steps}</ul></div>
                </div>
                """
            )

    st.html(
        """
        <div class="notice">ðŸ”” è¿åŠ¨æ—¶è¯·ä¿æŒè½»æ¾ã€‚è‹¥å¤´æ™•ã€èƒ¸é—·ã€å¿ƒæ…Œã€è…¿è„šç–¼ç—›æˆ–è¡€ç³–è¿‡ä½Žï¼Œè¯·é©¬ä¸Šåœæ­¢å¹¶è”ç³»å®¶äººæˆ–åŒ»ç”Ÿã€‚</div>
        """
    )


def glucose_zone(value: float) -> tuple[str, str]:
    if value < 70:
        return "å±é™©ï¼šè¡€ç³–åä½Ž", "red"
    if value <= 140:
        return "æ­£å¸¸èŒƒå›´", "green"
    if value <= 180:
        return "æ³¨æ„ï¼šè¡€ç³–åé«˜", "yellow"
    return "å±é™©ï¼šè¡€ç³–è¿‡é«˜", "red"


def glucose_module() -> None:
    page_header("è¡€ç³–è®°å½•", "è®°å½•æ¯æ—¥è¡€ç³–ï¼ŒæŸ¥çœ‹æœ€è¿‘30å¤©è¶‹åŠ¿å’Œé£Žé™©é¢œè‰²åŒºã€‚")

    with st.form("glucose_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            record_date = st.date_input("ðŸ“… æ—¥æœŸ", value=date.today())
        with col2:
            record_time = st.time_input("ðŸ•˜ æ—¶é—´", value=datetime.now().time().replace(second=0, microsecond=0))
        with col3:
            value = st.number_input("ðŸ©¸ è¡€ç³– mg/dL", min_value=30, max_value=500, value=120, step=1)

        period = st.selectbox("ðŸ½ï¸ æµ‹é‡æ—¶é—´", ["ç©ºè…¹", "æ—©é¤åŽ", "åˆé¤åŽ", "æ™šé¤åŽ", "ç¡å‰", "ä¸ç¡®å®š"])
        note = st.text_area("ðŸ“ å¤‡æ³¨", placeholder="ä¾‹å¦‚ï¼šä»Šå¤©é€æžã€åƒå¾—è¾ƒå¤šã€æ„Ÿè§‰å¤´æ™•")
        submitted = st.form_submit_button("âœ… ä¿å­˜è¡€ç³–è®°å½•")

    if submitted:
        st.session_state.glucose_records.append(
            {
                "æ—¥æœŸ": record_date.isoformat(),
                "æ—¶é—´": record_time.strftime("%H:%M"),
                "è¡€ç³–": int(value),
                "æµ‹é‡æ—¶é—´": period,
                "å¤‡æ³¨": note.strip(),
            }
        )
        zone_text, zone_color = glucose_zone(value)
        if zone_color == "green":
            st.html(f'<div class="alert-green">âœ… å·²ä¿å­˜ï¼š{escape(zone_text)}</div>')
        else:
            st.html(f'<div class="alert-red">âš ï¸ å·²ä¿å­˜ï¼š{escape(zone_text)}ï¼Œè¯·æŒ‰åŒ»ç”Ÿå»ºè®®å¤„ç†ã€‚</div>')

    records = pd.DataFrame(st.session_state.glucose_records)
    if records.empty:
        info_card("è¿˜æ²¡æœ‰è®°å½•", "è¯·å…ˆè¾“å…¥ä»Šå¤©çš„è¡€ç³–ã€‚ä¿å­˜åŽï¼Œè¿™é‡Œä¼šæ˜¾ç¤ºè¶‹åŠ¿å›¾ã€‚", "ðŸ©¸")
        return

    records["æ—¥æœŸæ—¶é—´"] = pd.to_datetime(records["æ—¥æœŸ"] + " " + records["æ—¶é—´"])
    records = records.sort_values("æ—¥æœŸæ—¶é—´")
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    recent = records[records["æ—¥æœŸæ—¶é—´"] >= cutoff].copy()

    last_value = float(records.iloc[-1]["è¡€ç³–"])
    last_text, last_color = glucose_zone(last_value)
    if last_color == "green":
        st.html(f'<div class="alert-green">âœ… æœ€æ–°è¡€ç³–ï¼š{int(last_value)} mg/dLï¼Œ{escape(last_text)}</div>')
    else:
        st.html(f'<div class="alert-red">ðŸš¨ æœ€æ–°è¡€ç³–ï¼š{int(last_value)} mg/dLï¼Œ{escape(last_text)}</div>')

    fig = go.Figure()
    if not recent.empty:
        x0 = recent["æ—¥æœŸæ—¶é—´"].min()
        x1 = recent["æ—¥æœŸæ—¶é—´"].max()
        if x0 == x1:
            x0 = x0 - pd.Timedelta(hours=12)
            x1 = x1 + pd.Timedelta(hours=12)

        fig.add_hrect(y0=40, y1=70, fillcolor="rgba(255, 92, 122, 0.18)", line_width=0)
        fig.add_hrect(y0=70, y1=140, fillcolor="rgba(0, 255, 136, 0.16)", line_width=0)
        fig.add_hrect(y0=140, y1=180, fillcolor="rgba(255, 209, 102, 0.18)", line_width=0)
        fig.add_hrect(y0=180, y1=500, fillcolor="rgba(255, 92, 122, 0.18)", line_width=0)
        fig.add_trace(
            go.Scatter(
                x=recent["æ—¥æœŸæ—¶é—´"],
                y=recent["è¡€ç³–"],
                mode="lines+markers",
                line=dict(color="#008f5f", width=4),
                marker=dict(size=12, color="#ffffff", line=dict(color="#008f5f", width=2)),
                text=recent["æµ‹é‡æ—¶é—´"],
                hovertemplate="%{x}<br>è¡€ç³–ï¼š%{y} mg/dL<br>%{text}<extra></extra>",
            )
        )
        fig.update_xaxes(range=[x0, x1])

    fig.update_layout(
        title="æœ€è¿‘30å¤©è¡€ç³–è¶‹åŠ¿",
        paper_bgcolor="#f7fafc",
        plot_bgcolor="#ffffff",
        font=dict(color="#17202a", size=18),
        height=470,
        margin=dict(l=20, r=20, t=60, b=20),
        yaxis=dict(title="mg/dL", range=[40, 260], gridcolor="rgba(23,32,42,0.12)"),
        xaxis=dict(title="æ—¥æœŸ", gridcolor="rgba(23,32,42,0.10)"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    section_title("æœ€è¿‘30å¤©åŽ†å²")
    display = recent.sort_values("æ—¥æœŸæ—¶é—´", ascending=False)[["æ—¥æœŸ", "æ—¶é—´", "è¡€ç³–", "æµ‹é‡æ—¶é—´", "å¤‡æ³¨"]]
    st.dataframe(display, use_container_width=True, hide_index=True)


def today_key(med_id: int, day: date | None = None) -> str:
    day = day or date.today()
    return f"{day.isoformat()}::{med_id}"


def status_for_med(med_id: int, day: date | None = None) -> str:
    return st.session_state.med_log.get(today_key(med_id, day), "pending")


def status_label(status: str) -> str:
    return {
        "taken": "âœ… å·²æœç”¨",
        "pending": "â° å¾…æœç”¨",
        "missed": "âŒ å·²å¿˜è®°",
    }.get(status, "â° å¾…æœç”¨")


def set_med_status(med_id: int, status: str) -> None:
    st.session_state.med_log[today_key(med_id)] = status

def set_all_meds_status(status: str) -> None:
    for med in st.session_state.medications:
        st.session_state.med_log[today_key(med["id"])] = status

def medication_module() -> None:
    page_header("ç”¨è¯æé†’", "æ·»åŠ è¯ç‰©ã€æŸ¥çœ‹ä»Šæ—¥æ¸…å•ï¼Œå¹¶è®°å½•æœ¬å‘¨æœè¯å®Œæˆæƒ…å†µã€‚")

    meds = st.session_state.medications
    pending_count = sum(1 for med in meds if status_for_med(med["id"]) == "pending")
    missed_count = sum(1 for med in meds if status_for_med(med["id"]) == "missed")
    taken_count = sum(1 for med in meds if status_for_med(med["id"]) == "taken")

    section_title("å¿«é€Ÿæ“ä½œ")
    st.html(
        f"""
        <div class="module-actions">
            <div class="module-action-card primary">
                <div class="big-icon">ðŸ’Š</div>
                <div class="module-action-title">ä»Šå¤©è¯ç‰©</div>
                <div class="module-action-desc">å·²æœç”¨ {taken_count} ä¸ªï¼Œå¾…æœç”¨ {pending_count} ä¸ªã€‚</div>
            </div>
            <div class="module-action-card {'alert' if missed_count else ''}">
                <div class="big-icon">â°</div>
                <div class="module-action-title">å¿˜è®°æé†’</div>
                <div class="module-action-desc">ä»Šå¤©å¿˜è®° {missed_count} ä¸ªè¯ã€‚éœ€è¦æ—¶å¯ä¸€é”®æ”¹å›žå¾…æœç”¨ã€‚</div>
            </div>
            <div class="module-action-card">
                <div class="big-icon">âž•</div>
                <div class="module-action-title">é©¬ä¸Šæ“ä½œ</div>
                <div class="module-action-desc">å…ˆç‚¹ä¸‹é¢çš„å¤§æŒ‰é’®ï¼Œå†çœ‹ä»Šå¤©çš„è¯ç‰©æ¸…å•ã€‚</div>
            </div>
        </div>
        """
    )
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("âœ… ä»Šå¤©å…¨éƒ¨å·²æœç”¨", key="all_meds_taken", use_container_width=True, disabled=not meds):
            set_all_meds_status("taken")
            st.rerun()
    with action_col2:
        if st.button("â° ä»Šå¤©å…¨éƒ¨æ”¹ä¸ºå¾…æœç”¨", key="all_meds_pending", use_container_width=True, disabled=not meds):
            set_all_meds_status("pending")
            st.rerun()

    with st.form("med_form", clear_on_submit=True):
        section_title("添加药物")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ðŸ’Š è¯ç‰©åç§°", placeholder="ä¾‹å¦‚ï¼šé™ç³–è¯ã€é™åŽ‹è¯ã€ç£·ç»“åˆå‰‚")
            dose = st.text_input("ðŸ“ å‰‚é‡", placeholder="ä¾‹å¦‚ï¼š1ç‰‡ã€5mg")
        with col2:
            frequency = st.text_input("ðŸ” é¢‘çŽ‡", placeholder="ä¾‹å¦‚ï¼šæ¯å¤©ã€æ¯12å°æ—¶ã€é€æžåŽã€å‘¨ä¸€ä¸‰äº”")
            take_time = st.selectbox("ðŸ•˜ æœè¯æ—¶é—´", ["æ—©ä¸Š", "ä¸­åˆ", "æ™šä¸Š", "ç¡å‰", "é€æžåŽ"])
        notes = st.text_area("ðŸ“ ç‰¹åˆ«è¯´æ˜Ž", placeholder="ä¾‹å¦‚ï¼šé¥­åŽæœç”¨ã€é…æ¸©æ°´ã€ä¸è¦å’ŒæŸè¯åŒæœ")
        add_med = st.form_submit_button("âž• æ·»åŠ è¯ç‰©")

    if add_med:
        if name.strip():
            st.session_state.medications.append(
                {
                    "id": time_ns(),
                    "name": name.strip(),
                    "dose": dose.strip() or "æŒ‰åŒ»å˜±",
                    "frequency": frequency.strip() or "æŒ‰åŒ»å˜±",
                    "time": take_time,
                    "notes": notes.strip(),
                }
            )
            st.html('<div class="alert-green">âœ… è¯ç‰©å·²æ·»åŠ </div>')
        else:
            st.html('<div class="alert-red">âš ï¸ è¯·å¡«å†™è¯ç‰©åç§°</div>')

    meds = st.session_state.medications
    if not meds:
        info_card("ä»Šæ—¥æ²¡æœ‰è¯ç‰©", "è¯·å…ˆæ·»åŠ åŒ»ç”Ÿå¼€å…·çš„è¯ç‰©ã€‚", "ðŸ’Š")
        return

    today_missed = [med for med in meds if status_for_med(med["id"]) == "missed"]
    if today_missed:
        names = "ã€".join(escape(med["name"]) for med in today_missed)
        st.html(f'<div class="alert-red">ðŸš¨ ä»Šå¤©æœ‰è¯ç‰©æ ‡è®°ä¸ºå¿˜è®°ï¼š{names}</div>')

    section_title("ä»Šæ—¥è¯ç‰©")
    for med in meds:
        current = status_for_med(med["id"])
        color = {"taken": "#008f5f", "pending": "#a46a00", "missed": "#c62845"}[current]
        st.html(
            f"""
            <div class="card" style="border-color: rgba(255,255,255,0.14);">
                <div class="pill" style="color:{color}; border:1px solid {color}; background:#ffffff;">
                    {status_label(current)}
                </div>
                <div class="card-title">{escape(med["name"])}</div>
                <div class="big-text"><b>å‰‚é‡ï¼š</b>{escape(med["dose"])}</div>
                <div class="big-text"><b>é¢‘çŽ‡ï¼š</b>{escape(med["frequency"])}</div>
                <div class="big-text"><b>æ—¶é—´ï¼š</b>{escape(med["time"])}</div>
                <div class="big-text muted"><b>è¯´æ˜Žï¼š</b>{escape(med["notes"] or "æ— ")}</div>
            </div>
            """
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("âœ… å·²æœç”¨", key=f"taken_{med['id']}"):
                set_med_status(med["id"], "taken")
                st.rerun()
        with b2:
            if st.button("â° å¾…æœç”¨", key=f"pending_{med['id']}"):
                set_med_status(med["id"], "pending")
                st.rerun()
        with b3:
            if st.button("âŒ å¿˜è®°äº†", key=f"missed_{med['id']}"):
                set_med_status(med["id"], "missed")
                st.rerun()

    section_title("æœ¬å‘¨æœè¯è®°å½•")
    rows = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        statuses = [status_for_med(med["id"], day) for med in meds]
        rows.append(
            {
                "æ—¥æœŸ": day.strftime("%m-%d"),
                "å·²æœç”¨": statuses.count("taken"),
                "å¾…æœç”¨": statuses.count("pending"),
                "å¿˜è®°": statuses.count("missed"),
            }
        )
    weekly = pd.DataFrame(rows)
    st.dataframe(weekly, use_container_width=True, hide_index=True)


def go_to_module(module_name: str) -> None:
    st.session_state.current_module = module_name
    st.rerun()


def today_meal_names() -> str:
    try:
        weekly_plan = build_generated_meal_plan(date.today())
        today_plan = weekly_plan[date.today().weekday()]
        return " / ".join(meal["name"] for meal in today_plan["meals"])
    except Exception:
        return "æŸ¥çœ‹ä»Šæ—¥ä¸‰é¤è®¡åˆ’"


def today_overview_cards() -> list[dict]:
    today_name = WEEK_DAYS[date.today().weekday()]
    is_dialysis = today_name in st.session_state.dialysis_days
    pending_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "pending")
    missed_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "missed")
    latest_glucose = (
        f"{st.session_state.glucose_records[-1]['è¡€ç³–']} mg/dL"
        if st.session_state.glucose_records
        else "ä»Šå¤©è¿˜æ²¡æœ‰è®°å½•"
    )
    return [
        {
            "icon": "ðŸ©º",
            "title": "ä»Šå¤©å®‰æŽ’",
            "desc": "ä»Šå¤©æ˜¯é€æžæ—¥ï¼Œè¯·ä¼‘æ¯ã€‚" if is_dialysis else "ä»Šå¤©ä¸æ˜¯é€æžæ—¥ï¼Œå¯ä»¥åšè½»æ´»åŠ¨ã€‚",
            "style": "primary" if is_dialysis else "",
        },
        {
            "icon": "ðŸ’Š",
            "title": "è¯ç‰©çŠ¶æ€",
            "desc": f"å¾…æœç”¨ {pending_meds} ä¸ªï¼Œå¿˜è®° {missed_meds} ä¸ªã€‚" if st.session_state.medications else "è¿˜æ²¡æœ‰æ·»åŠ è¯ç‰©ã€‚",
            "style": "primary" if missed_meds else "",
        },
        {
            "icon": "ðŸ©¸",
            "title": "æœ€è¿‘è¡€ç³–",
            "desc": latest_glucose,
            "style": "",
        },
        {
            "icon": "ðŸ½ï¸",
            "title": "ä»Šå¤©ä¸‰é¤",
            "desc": today_meal_names(),
            "style": "",
        },
    ]


def lobby_reminders() -> list[dict]:
    today_name = WEEK_DAYS[date.today().weekday()]
    is_dialysis = today_name in st.session_state.dialysis_days
    pending_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "pending")
    missed_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "missed")

    reminders = [
        {
            "icon": "ðŸ½ï¸",
            "title": "ä»Šæ—¥é¥®é£Ÿ",
            "desc": today_meal_names(),
        },
        {
            "icon": "ðŸ’Š",
            "title": "ç”¨è¯æé†’",
            "desc": f"å¾…æœç”¨ {pending_meds} ä¸ªï¼Œå·²å¿˜è®° {missed_meds} ä¸ªã€‚" if st.session_state.medications else "è¿˜æ²¡æœ‰æ·»åŠ è¯ç‰©ã€‚",
        },
    ]

    if is_dialysis:
        reminders.append(
            {
                "icon": "ðŸ©º",
                "title": "ä»Šå¤©æ˜¯é€æžæ—¥",
                "desc": "ä¸è¦å®‰æŽ’è¿åŠ¨ï¼Œæ³¨æ„ä¼‘æ¯ï¼Œé¥®é£Ÿå’Œé¥®æ°´æŒ‰åŒ»æŠ¤å»ºè®®æ‰§è¡Œã€‚",
            }
        )
    else:
        reminders.append(
            {
                "icon": "ðŸš¶",
                "title": "ä»Šæ—¥è¿åŠ¨",
                "desc": "å¯ä»¥é€‰æ‹©è½»æ¾æ­¥è¡Œ15-20åˆ†é’Ÿï¼Œæˆ–åšåå§¿ä¼¸å±•ã€‚",
            }
        )

    if st.session_state.glucose_records:
        latest = st.session_state.glucose_records[-1]
        reminders.append(
            {
                "icon": "ðŸ©¸",
                "title": "æœ€è¿‘è¡€ç³–",
                "desc": f"{latest.get('è¡€ç³–', '-') } mg/dLï¼Œè®°å¾—ç»§ç»­è®°å½•è¶‹åŠ¿ã€‚",
            }
        )
    else:
        reminders.append(
            {
                "icon": "ðŸ©¸",
                "title": "è¡€ç³–è®°å½•",
                "desc": "ä»Šå¤©è¿˜æ²¡æœ‰è¡€ç³–è®°å½•ï¼Œå»ºè®®æµ‹é‡åŽä¿å­˜ã€‚",
            }
        )

    reminders.append(
        {
            "icon": "ðŸ“·",
            "title": "AIå¥åº·è§‚å¯Ÿ",
            "desc": "å¦‚æ„Ÿè§‰è„¸è‚¿ã€ç–²åŠ³ã€èƒ¸é—·æˆ–çŠ¶æ€å˜å·®ï¼Œå¯ä»¥æ‹ç…§å¹¶å¡«å†™ç—‡çŠ¶ã€‚",
        }
    )
    return reminders


def action_card_hint(module_name: str) -> str:
    hints = {
        "é¥®é£ŸåŠ©æ‰‹": "çœ‹ä»Šå¤©åƒä»€ä¹ˆ",
        "è¿åŠ¨è®¡åˆ’": "çœ‹ä»Šå¤©åŠ¨ä¸€åŠ¨",
        "è¡€ç³–è®°å½•": "é©¬ä¸Šè®°è¡€ç³–",
        "ç”¨è¯æé†’": "çœ‹ä»Šå¤©è¦åƒçš„è¯",
        "AIå¥åº·è§‚å¯Ÿ": "æ‹ç…§çœ‹çŠ¶æ€",
    }
    return hints.get(module_name, "ç‚¹ä¸€ä¸‹è¿›å…¥")

def render_lobby_calendar() -> None:
    week_start = week_start_for(date.today())
    today_index = date.today().weekday()
    boxes = []
    for index, day_name in enumerate(WEEK_DAYS):
        day = week_start + timedelta(days=index)
        classes = ["calendar-day"]
        if index == today_index:
            classes.append("today")
        is_dialysis = day_name in st.session_state.dialysis_days
        if is_dialysis:
            classes.append("dialysis")
        note = "é€æž" if is_dialysis else "è½»æ´»åŠ¨"
        if index == today_index:
            note = f"ä»Šå¤© Â· {note}"
        boxes.append(
            f"""
            <div class="{' '.join(classes)}">
                <div class="calendar-name">{escape(day_name)}</div>
                <div class="calendar-date">{day.strftime('%m-%d')}</div>
                <div class="calendar-note">{escape(note)}</div>
            </div>
            """
        )
    st.html(f'<div class="calendar-strip">{"".join(boxes)}</div>')


def home_module() -> None:
    st.html(
        """
        <div class="lobby-hero">
            <div class="lobby-title">ðŸ’š ä»Šæ—¥ç…§æŠ¤é¦–é¡µ</div>
            <div class="lobby-subtitle">å…ˆçœ‹ä»Šå¤©è¦åšä»€ä¹ˆï¼Œå†ç‚¹å¤§æŒ‰é’®è¿›å…¥åŠŸèƒ½ã€‚</div>
        </div>
        """
    )

    section_title("ä»Šå¤©å…ˆåšè¿™äº›")
    overview_cards = today_overview_cards()
    top_cols = st.columns(2)
    for index, card in enumerate(overview_cards):
        with top_cols[index % 2]:
            st.html(
                f"""
                <div class="quick-card {'primary' if card['style'] else ''}">
                    <div class="big-icon">{escape(card["icon"])}</div>
                    <div class="quick-title">{escape(card["title"])}</div>
                    <div class="quick-desc">{escape(card["desc"])}</div>
                </div>
                """
            )

    section_title("ç‚¹ä¸€ä¸‹è¿›å…¥")
    st.html('<div class="section-tip">åªçœ‹å¤§å›¾æ ‡å’Œå¤§æŒ‰é’®ï¼Œå°±å¯ä»¥è¿›å…¥å¯¹åº”åŠŸèƒ½ã€‚</div>')
    cards = [
        ("é¥®é£ŸåŠ©æ‰‹", "ðŸ½ï¸"),
        ("è¿åŠ¨è®¡åˆ’", "ðŸš¶"),
        ("è¡€ç³–è®°å½•", "ðŸ©¸"),
        ("ç”¨è¯æé†’", "ðŸ’Š"),
        ("AIå¥åº·è§‚å¯Ÿ", "ðŸ“·"),
    ]

    for start in range(0, len(cards), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            if start + offset >= len(cards):
                continue
            module_name, icon = cards[start + offset]
            with col:
                st.html(
                    f"""
                    <div class="action-card {'primary' if module_name == 'é¥®é£ŸåŠ©æ‰‹' else ''}">
                        <div class="action-icon">{escape(icon)}</div>
                        <div class="action-title">{escape(module_name)}</div>
                        <div class="action-hint">{escape(action_card_hint(module_name))}</div>
                    </div>
                    """
                )
                if st.button(f"æ‰“å¼€ {module_name}", key=f"home_{module_name}", use_container_width=True):
                    go_to_module(module_name)

    section_title("æœ¬å‘¨æ—¥åŽ†")
    render_lobby_calendar()

    section_title("ä»Šæ—¥æé†’")
    for item in lobby_reminders():
        st.html(
            f"""
            <div class="todo-item">
                <div class="todo-icon">{escape(item["icon"])}</div>
                <div>
                    <div class="todo-title">{escape(item["title"])}</div>
                    <div class="todo-desc">{escape(item["desc"])}</div>
                </div>
            </div>
            """
        )

def load_face_image(uploaded_file) -> Image.Image | None:
    if uploaded_file is None:
        return None
    try:
        image = Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")
        image.thumbnail((900, 900))
        return image
    except Exception:
        return None


def face_photo_metrics(image: Image.Image) -> dict:
    resized = image.resize((160, 160))
    stat = ImageStat.Stat(resized)
    r, g, b = stat.mean
    brightness = (r + g + b) / 3
    redness = r - ((g + b) / 2)
    channel_spread = max(stat.stddev)
    quality = "æ¸…æ¥š"
    if brightness < 65:
        quality = "ç…§ç‰‡åæš—"
    elif brightness > 220:
        quality = "ç…§ç‰‡è¿‡äº®"
    elif channel_spread < 22:
        quality = "ç»†èŠ‚åå°‘"
    return {
        "brightness": round(brightness, 1),
        "redness": round(redness, 1),
        "quality": quality,
    }


def compare_photo_metrics(current: dict, baseline: dict | None) -> list[str]:
    if not baseline:
        return ["è¿˜æ²¡æœ‰åŸºå‡†ç…§ç‰‡ï¼Œæœ¬æ¬¡ç»“æžœä¼šä½œä¸ºä»¥åŽæ¯”è¾ƒçš„å‚è€ƒã€‚"]

    notes = []
    brightness_delta = current["brightness"] - baseline["brightness"]
    redness_delta = current["redness"] - baseline["redness"]

    if abs(brightness_delta) > 28:
        notes.append("ç…§ç‰‡æ˜Žæš—å’ŒåŸºå‡†å·®å¼‚è¾ƒå¤§ï¼Œæ¯”è¾ƒç»“æžœå¯èƒ½ä¸å‡†ç¡®ã€‚")
    if redness_delta > 16:
        notes.append("ç…§ç‰‡é¢œè‰²æ¯”åŸºå‡†æ›´çº¢ï¼Œå¯èƒ½ä¸Žå…‰çº¿ã€çš®è‚¤çŠ¶æ€æˆ–ä¸é€‚æœ‰å…³ã€‚")
    elif redness_delta < -16:
        notes.append("ç…§ç‰‡é¢œè‰²æ¯”åŸºå‡†æ›´æ·¡ï¼Œå¯èƒ½ä¸Žå…‰çº¿æˆ–é¢è‰²å˜åŒ–æœ‰å…³ã€‚")
    if not notes:
        notes.append("ç…§ç‰‡é¢œè‰²å’Œæ˜Žæš—ä¸ŽåŸºå‡†æŽ¥è¿‘ã€‚")
    return notes


def risk_level(score: int) -> tuple[str, str, str]:
    if score >= 75:
        return "é«˜é£Žé™©", "#c62845", "è¯·å°½å¿«è”ç³»åŒ»ç”Ÿã€é€æžä¸­å¿ƒæˆ–å®¶äººï¼›è‹¥æœ‰èƒ¸ç—›ã€å‘¼å¸å›°éš¾ã€æ„è¯†ä¸æ¸…ï¼Œè¯·ç«‹å³æ€¥æ•‘ã€‚"
    if score >= 45:
        return "éœ€è¦æ³¨æ„", "#a46a00", "ä»Šå¤©éœ€è¦å¯†åˆ‡è§‚å¯Ÿï¼Œå¤æŸ¥è¡€ç³–ã€è¡€åŽ‹å’Œä½“é‡ï¼Œå¹¶è€ƒè™‘è”ç³»åŒ»æŠ¤äººå‘˜ã€‚"
    return "ç¨³å®š", "#008f5f", "ç›®å‰è®°å½•çœ‹èµ·æ¥è¾ƒç¨³å®šï¼Œè¯·ç»§ç»­æŒ‰è®¡åˆ’é¥®é£Ÿã€ç”¨è¯ã€é€æžå’Œè®°å½•ã€‚"


def add_factor(factors: list[dict], name: str, points: int, description: str, advice: str) -> None:
    if points <= 0:
        return
    factors.append(
        {
            "é¡¹ç›®": name,
            "åˆ†æ•°": points,
            "è¯´æ˜Ž": description,
            "å»ºè®®": advice,
        }
    )


def recent_glucose_default() -> int:
    if not st.session_state.glucose_records:
        return 120
    try:
        return int(st.session_state.glucose_records[-1]["è¡€ç³–"])
    except Exception:
        return 120


def missed_med_count_today() -> int:
    return sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "missed")


def build_ai_support_assessment(
    *,
    metrics: dict,
    baseline_metrics: dict | None,
    symptoms: dict,
    glucose_now: int,
    systolic: int,
    weight_gain: float,
    is_dialysis_day: bool,
    missed_meds: int,
    salty_food: int,
    fluid_extra: int,
    sweet_food: int,
    previous_score: int | None,
) -> dict:
    factors: list[dict] = []

    add_factor(
        factors,
        "å‘¼å¸å›°éš¾æˆ–èƒ¸é—·",
        symptoms["breath"] * 16,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['breath']}/3ã€‚",
        "å¦‚æžœæœ‰æ˜Žæ˜¾å‘¼å¸å›°éš¾ã€èƒ¸ç—›æˆ–ä¸èƒ½å¹³èººï¼Œè¯·ç«‹å³è”ç³»åŒ»ç”Ÿæˆ–æ€¥æ•‘ã€‚",
    )
    add_factor(
        factors,
        "æ„è¯†æˆ–ååº”å˜åŒ–",
        symptoms["confusion"] * 18,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['confusion']}/3ã€‚",
        "æ„è¯†ä¸æ¸…ã€ååº”æ˜Žæ˜¾å˜æ…¢å±žäºŽå±é™©ä¿¡å·ï¼Œåº”å°½å¿«å¯»æ±‚åŒ»ç–—å¸®åŠ©ã€‚",
    )
    add_factor(
        factors,
        "è„¸éƒ¨æˆ–çœ¼çš®æµ®è‚¿",
        symptoms["swelling"] * 9,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['swelling']}/3ã€‚",
        "è§‚å¯Ÿæ˜¯å¦æ°´åˆ†æˆ–ç›åˆ†è¿‡å¤šï¼›è®°å½•ä½“é‡ï¼Œå¹¶å‘ŠçŸ¥é€æžå›¢é˜Ÿã€‚",
    )
    add_factor(
        factors,
        "è…¿è„šæ°´è‚¿",
        symptoms["edema"] * 10,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['edema']}/3ã€‚",
        "æŠ¬é«˜åŒè…¿ï¼Œæ£€æŸ¥ä½“é‡å˜åŒ–ï¼›è‹¥è¶Šæ¥è¶Šè‚¿ï¼Œè¯·è”ç³»é€æžä¸­å¿ƒã€‚",
    )
    add_factor(
        factors,
        "å¤´æ™•æˆ–ç«™ä¸ç¨³",
        symptoms["dizziness"] * 8,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['dizziness']}/3ã€‚",
        "å…ˆåä¸‹ä¼‘æ¯ï¼Œæ£€æŸ¥è¡€ç³–å’Œè¡€åŽ‹ï¼›ä¸è¦ç‹¬è‡ªå¤–å‡ºã€‚",
    )
    add_factor(
        factors,
        "æ¶å¿ƒæˆ–å‘•å",
        symptoms["nausea"] * 6,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['nausea']}/3ã€‚",
        "å°‘é‡è¿›é£Ÿï¼Œè®°å½•å‘ç”Ÿæ—¶é—´ï¼›è‹¥æŒç»­å‘•åè¯·è”ç³»åŒ»ç”Ÿã€‚",
    )
    add_factor(
        factors,
        "æ˜Žæ˜¾ç–²åŠ³",
        symptoms["tired"] * 6,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['tired']}/3ã€‚",
        "å‡å°‘è¿åŠ¨ï¼Œæ³¨æ„ä¼‘æ¯ï¼›è‹¥çªç„¶æ˜Žæ˜¾åŠ é‡ï¼Œéœ€è¦è”ç³»åŒ»æŠ¤äººå‘˜ã€‚",
    )
    add_factor(
        factors,
        "é£Ÿæ¬²å˜å·®",
        symptoms["appetite"] * 4,
        f"ä¸¥é‡ç¨‹åº¦ï¼š{symptoms['appetite']}/3ã€‚",
        "å°‘é‡å¤šé¤ï¼Œä¼˜å…ˆä¿è¯åŒ»ç”Ÿå…è®¸çš„ä¼˜è´¨è›‹ç™½ã€‚",
    )

    if glucose_now < 70:
        glucose_points = 25
        glucose_desc = f"è¡€ç³– {glucose_now} mg/dLï¼Œä½ŽäºŽ70ã€‚"
        glucose_advice = "æŒ‰ä½Žè¡€ç³–å¤„ç†æ–¹æ¡ˆå¤„ç†ï¼Œå¹¶è”ç³»å®¶äººæˆ–åŒ»ç”Ÿï¼›ä¸¥é‡ç—‡çŠ¶è¯·æ€¥æ•‘ã€‚"
    elif glucose_now > 300:
        glucose_points = 25
        glucose_desc = f"è¡€ç³– {glucose_now} mg/dLï¼Œæ˜Žæ˜¾è¿‡é«˜ã€‚"
        glucose_advice = "æŒ‰åŒ»ç”Ÿç»™çš„é«˜è¡€ç³–æ–¹æ¡ˆå¤„ç†ï¼Œè¡¥å……è®°å½•é¥®é£Ÿå’Œè¯ç‰©ï¼Œå¿…è¦æ—¶è”ç³»åŒ»ç”Ÿã€‚"
    elif glucose_now > 250:
        glucose_points = 18
        glucose_desc = f"è¡€ç³– {glucose_now} mg/dLï¼Œåé«˜ã€‚"
        glucose_advice = "å¤æŸ¥è¡€ç³–ï¼Œå‡å°‘ä¸»é£Ÿå’Œç”œé£Ÿï¼Œç¡®è®¤é™ç³–è¯æ˜¯å¦æŒ‰æ—¶ä½¿ç”¨ã€‚"
    elif glucose_now > 180:
        glucose_points = 10
        glucose_desc = f"è¡€ç³– {glucose_now} mg/dLï¼Œéœ€è¦æ³¨æ„ã€‚"
        glucose_advice = "ä¸‹ä¸€é¤å‡å°‘ä¸»é£Ÿï¼Œé¿å…ç”œé¥®æ–™ï¼Œå¹¶ç»§ç»­è®°å½•ã€‚"
    else:
        glucose_points = 0
        glucose_desc = ""
        glucose_advice = ""
    add_factor(factors, "è¡€ç³–", glucose_points, glucose_desc, glucose_advice)

    if systolic >= 180:
        bp_points = 24
        bp_desc = f"æ”¶ç¼©åŽ‹ {systolic} mmHgï¼Œå±žäºŽå±é™©èŒƒå›´ã€‚"
        bp_advice = "å®‰é™ä¼‘æ¯åŽå¤æµ‹ï¼›è‹¥ä»å¾ˆé«˜æˆ–æœ‰èƒ¸ç—›å¤´ç—›ï¼Œè¯·ç«‹å³è”ç³»åŒ»ç”Ÿã€‚"
    elif systolic >= 160:
        bp_points = 14
        bp_desc = f"æ”¶ç¼©åŽ‹ {systolic} mmHgï¼Œåé«˜ã€‚"
        bp_advice = "å‡å°‘ç›åˆ†ï¼Œå¤æµ‹è¡€åŽ‹ï¼Œç¡®è®¤é™åŽ‹è¯æ˜¯å¦æŒ‰æ—¶æœç”¨ã€‚"
    elif systolic <= 90:
        bp_points = 18
        bp_desc = f"æ”¶ç¼©åŽ‹ {systolic} mmHgï¼Œåä½Žã€‚"
        bp_advice = "åä¸‹æˆ–èººä¸‹ä¼‘æ¯ï¼Œé¿å…ç«™ç«‹ï¼›è‹¥å¤´æ™•æ˜Žæ˜¾è¯·è”ç³»åŒ»æŠ¤äººå‘˜ã€‚"
    else:
        bp_points = 0
        bp_desc = ""
        bp_advice = ""
    add_factor(factors, "è¡€åŽ‹", bp_points, bp_desc, bp_advice)

    if weight_gain >= 3.0:
        weight_points = 20
        weight_desc = f"ä¸¤æ¬¡é€æžé—´å¢žåŠ  {weight_gain:.1f} kgï¼Œåå¤šã€‚"
        weight_advice = "é™åˆ¶ç›å’Œæ¶²ä½“ï¼Œå°½å¿«å‘ŠçŸ¥é€æžä¸­å¿ƒã€‚"
    elif weight_gain >= 2.0:
        weight_points = 10
        weight_desc = f"ä¸¤æ¬¡é€æžé—´å¢žåŠ  {weight_gain:.1f} kgï¼Œéœ€è¦æ³¨æ„ã€‚"
        weight_advice = "ä»Šå¤©å‡å°‘å’¸é£Ÿå’Œæ±¤æ°´ï¼Œç»§ç»­è®°å½•ä½“é‡ã€‚"
    else:
        weight_points = 0
        weight_desc = ""
        weight_advice = ""
    add_factor(factors, "é€æžé—´ä½“é‡å¢žåŠ ", weight_points, weight_desc, weight_advice)

    add_factor(
        factors,
        "ä»Šå¤©æ˜¯é€æžæ—¥",
        4 if is_dialysis_day else 0,
        "é€æžæ—¥å‰åŽèº«ä½“æ›´å®¹æ˜“ç–²åŠ³æˆ–ä¸èˆ’æœã€‚",
        "é€æžæ—¥é¿å…è¿åŠ¨ï¼ŒæŒ‰åŒ»æŠ¤å»ºè®®é¥®é£Ÿå’Œé¥®æ°´ã€‚",
    )
    add_factor(
        factors,
        "å¿˜è®°ç”¨è¯",
        min(18, missed_meds * 9),
        f"ä»Šå¤©æ ‡è®°å¿˜è®° {missed_meds} ä¸ªè¯ç‰©ã€‚",
        "ä¸è¦è‡ªè¡Œè¡¥åŒå€å‰‚é‡ï¼›æŒ‰åŒ»å˜±æˆ–è”ç³»åŒ»ç”Ÿ/è¯å¸ˆç¡®è®¤ã€‚",
    )
    add_factor(
        factors,
        "æœ€è¿‘åƒå’¸",
        salty_food * 5,
        f"å’¸é£Ÿç¨‹åº¦ï¼š{salty_food}/3ã€‚",
        "å‡å°‘é…±æ²¹ã€å’¸èœã€è…Œåˆ¶å“ï¼›è§‚å¯Ÿå£æ¸´ã€è¡€åŽ‹å’Œæ°´è‚¿ã€‚",
    )
    add_factor(
        factors,
        "æ¶²ä½“å¯èƒ½åå¤š",
        fluid_extra * 6,
        f"é¥®æ°´/æ±¤/ç²¥/èŒ¶åå¤šç¨‹åº¦ï¼š{fluid_extra}/3ã€‚",
        "æ±¤æ°´ã€ç²¥æ°´ã€èŒ¶éƒ½è®¡å…¥æ¶²ä½“ï¼›æŒ‰é€æžå›¢é˜Ÿç»™çš„æ¯æ—¥é™åˆ¶æ‰§è¡Œã€‚",
    )
    add_factor(
        factors,
        "ç”œé£Ÿæˆ–ä¸»é£Ÿåå¤š",
        sweet_food * 6,
        f"ç”œé£Ÿæˆ–ä¸»é£Ÿåå¤šç¨‹åº¦ï¼š{sweet_food}/3ã€‚",
        "é¿å…ç³–ã€ç”œé¥®æ–™ï¼›ç±³é¥­ã€é¢ã€ç²¥æŽ§åˆ¶å°åŠç¢—ã€‚",
    )

    if metrics["quality"] != "æ¸…æ¥š":
        add_factor(
            factors,
            "ç…§ç‰‡è´¨é‡",
            4,
            f"æœ¬æ¬¡ç…§ç‰‡ï¼š{metrics['quality']}ã€‚",
            "ä¸‹æ¬¡ç”¨æ­£é¢ã€æ˜Žäº®ã€åŒä¸€ä½ç½®æ‹ç…§ï¼Œæ¯”è¾ƒä¼šæ›´å¯é ã€‚",
        )

    photo_notes = compare_photo_metrics(metrics, baseline_metrics)
    if baseline_metrics:
        redness_delta = metrics["redness"] - baseline_metrics["redness"]
        if abs(redness_delta) > 18:
            add_factor(
                factors,
                "é¢è‰²å˜åŒ–",
                6,
                "ç…§ç‰‡é¢œè‰²å’ŒåŸºå‡†ç…§ç‰‡æœ‰æ˜Žæ˜¾å·®å¼‚ã€‚",
                "å…ˆç¡®è®¤å…‰çº¿æ˜¯å¦ç›¸åŒï¼›è‹¥åŒæ—¶æœ‰ä¸é€‚ç—‡çŠ¶ï¼Œè¯·è”ç³»åŒ»æŠ¤äººå‘˜ã€‚",
            )

    rule_score = min(100, sum(item["åˆ†æ•°"] for item in factors))
    ai_result = predict_ai_risk(
        {
            "glucose": glucose_now,
            "systolic": systolic,
            "weight_gain": weight_gain,
            "swelling": symptoms["swelling"],
            "tired": symptoms["tired"],
            "appetite": symptoms["appetite"],
            "breath": symptoms["breath"],
            "dizziness": symptoms["dizziness"],
            "nausea": symptoms["nausea"],
            "edema": symptoms["edema"],
            "confusion": symptoms["confusion"],
            "dialysis_day": 1 if is_dialysis_day else 0,
            "missed_meds": missed_meds,
            "salty_food": salty_food,
            "fluid_extra": fluid_extra,
            "sweet_food": sweet_food,
            "photo_quality_bad": 1 if metrics["quality"] != "æ¸…æ¥š" else 0,
            "face_color_change": 1 if baseline_metrics and abs(metrics["redness"] - baseline_metrics["redness"]) > 18 else 0,
        }
    )
    raw_score = int(round((rule_score * 0.65) + (ai_result["score"] * 0.35)))
    level, color, recommendation = risk_level(raw_score)

    if previous_score is None:
        trend = "ç¬¬ä¸€æ¬¡è®°å½•ï¼Œæš‚æ— è¶‹åŠ¿æ¯”è¾ƒã€‚"
    elif raw_score <= previous_score - 10:
        trend = "æ¯”ä¸Šæ¬¡æ›´ç¨³å®šï¼Œå¯èƒ½åœ¨æ”¹å–„ã€‚"
    elif raw_score >= previous_score + 10:
        trend = "æ¯”ä¸Šæ¬¡æ›´éœ€è¦æ³¨æ„ï¼Œå¯èƒ½åœ¨å˜å·®ã€‚"
    else:
        trend = "å’Œä¸Šæ¬¡æŽ¥è¿‘ï¼Œå˜åŒ–ä¸æ˜Žæ˜¾ã€‚"

    top_factors = sorted(factors, key=lambda item: item["åˆ†æ•°"], reverse=True)[:5]
    if raw_score >= 75:
        summary = "æœ¬æ¬¡ç»“æžœæç¤ºé«˜é£Žé™©ã€‚è¯·ä¼˜å…ˆå¤„ç†å‘¼å¸ã€æ„è¯†ã€è¡€ç³–ã€è¡€åŽ‹æˆ–æ°´è‚¿ç­‰å±é™©ä¿¡å·ã€‚"
    elif raw_score >= 45:
        summary = "æœ¬æ¬¡ç»“æžœæç¤ºéœ€è¦æ³¨æ„ã€‚å»ºè®®ä»Šå¤©åŠ å¼ºè§‚å¯Ÿï¼Œå¹¶å¤æŸ¥è¡€ç³–ã€è¡€åŽ‹å’Œä½“é‡ã€‚"
    else:
        summary = "æœ¬æ¬¡ç»“æžœæ•´ä½“è¾ƒç¨³å®šã€‚ç»§ç»­ä¿æŒé¥®é£Ÿã€ç”¨è¯ã€é€æžå’Œè®°å½•ã€‚"

    return {
        "score": raw_score,
        "rule_score": rule_score,
        "ai_score": ai_result["score"],
        "ai_level": ai_result["level"],
        "model_name": ai_result["model"],
        "model_loss": ai_result["training_loss"],
        "level": level,
        "color": color,
        "recommendation": recommendation,
        "trend": trend,
        "summary": summary,
        "photo_notes": photo_notes,
        "factors": factors,
        "top_factors": top_factors,
    }


def face_observation_module() -> None:
    page_header("AI健康观察", "用照片、症状、血糖、血压、体重和用药记录生成可解释的风险评分。")

    st.html(
        """
        <div class="notice">
        📷 重要说明：这不是医学诊断。本功能是原型AI辅助观察，会把照片质量、症状、血糖、血压、体重、透析、用药和饮食情况合在一起评分。若症状严重，请不要等评分，直接联系医生或急救。
        </div>
        """
    )
    st.html(f'<div class="notice">🤖 {escape(model_card_text())}</div>')

    section_title("快速操作")
    st.html(
        """
        <div class="module-actions">
            <div class="module-action-card primary">
                <div class="big-icon">📸</div>
                <div class="module-action-title">现在拍照</div>
                <div class="module-action-desc">手机或电脑直接拍正面照片。</div>
            </div>
            <div class="module-action-card">
                <div class="big-icon">🖼️</div>
                <div class="module-action-title">上传照片</div>
                <div class="module-action-desc">如果已经拍好照片，就直接上传。</div>
            </div>
            <div class="module-action-card alert">
                <div class="big-icon">🧹</div>
                <div class="module-action-title">清理记录</div>
                <div class="module-action-desc">如果想重新开始，可以清除观察历史。</div>
            </div>
        </div>
        """
    )
    action_face_1, action_face_2, action_face_3 = st.columns(3)
    with action_face_1:
        if st.button("📸 用摄像头拍照", key="face_use_camera", use_container_width=True):
            st.session_state.face_photo_source = "camera"
            st.rerun()
    with action_face_2:
        if st.button("🖼️ 改为上传照片", key="face_use_upload", use_container_width=True):
            st.session_state.face_photo_source = "upload"
            st.rerun()
    with action_face_3:
        if st.button("🧹 清除观察历史", key="face_clear_history_top", use_container_width=True):
            st.session_state.face_history = []
            st.html('<div class="alert-green">✅ 已清除观察历史。</div>')
    st.session_state.hospital_phone = st.text_input(
        "â˜Žï¸ åŒ»é™¢æˆ–é€æžä¸­å¿ƒç”µè¯ï¼ˆå¯é€‰ï¼‰",
        value=st.session_state.hospital_phone,
        placeholder="ä¾‹å¦‚ï¼š120 æˆ– åŒ»é™¢ç”µè¯",
    )

    source_options = ["æ‰‹æœº/ç”µè„‘æ‘„åƒå¤´æ‹ç…§", "ä¸Šä¼ ç…§ç‰‡"]
    default_source = 0 if st.session_state.face_photo_source == "camera" else 1
    source = st.selectbox("ðŸ“¸ é€‰æ‹©ç…§ç‰‡æ–¹å¼", source_options, index=default_source)
    st.session_state.face_photo_source = "camera" if source == source_options[0] else "upload"
    if source == "æ‰‹æœº/ç”µè„‘æ‘„åƒå¤´æ‹ç…§":
        photo_file = st.camera_input("è¯·æ­£é¢å¯¹ç€é•œå¤´ï¼Œå…‰çº¿æ˜Žäº®ï¼Œä¸æˆ´å£ç½©å’Œå¢¨é•œ")
    else:
        photo_file = st.file_uploader("ä¸Šä¼ æ­£é¢è„¸éƒ¨ç…§ç‰‡", type=["png", "jpg", "jpeg"])

    image = load_face_image(photo_file)
    if image is not None:
        st.image(image, caption="æœ¬æ¬¡ç…§ç‰‡", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        swelling = st.slider("çœ¼çš®æˆ–è„¸éƒ¨æµ®è‚¿", 0, 3, 0, help="0æ²¡æœ‰ï¼Œ3æ˜Žæ˜¾")
        tired = st.slider("æ˜Žæ˜¾ç–²åŠ³æˆ–ç²¾ç¥žå·®", 0, 3, 0)
        appetite = st.slider("é£Ÿæ¬²å˜å·®", 0, 3, 0)
        breath = st.slider("å‘¼å¸å›°éš¾æˆ–èƒ¸é—·", 0, 3, 0)
    with col2:
        dizziness = st.slider("å¤´æ™•ã€ç«™ä¸ç¨³", 0, 3, 0)
        nausea = st.slider("æ¶å¿ƒã€å‘•å", 0, 3, 0)
        edema = st.slider("è„šè¸æˆ–è…¿éƒ¨æ°´è‚¿", 0, 3, 0)
        confusion = st.slider("ååº”å˜æ…¢æˆ–æ„è¯†ä¸æ¸…", 0, 3, 0)

    section_title("åŸºç¡€æ•°æ®")
    latest_glucose = recent_glucose_default()
    today_name = WEEK_DAYS[date.today().weekday()]
    default_is_dialysis_day = today_name in st.session_state.dialysis_days
    today_missed_meds = missed_med_count_today()

    col3, col4, col5 = st.columns(3)
    with col3:
        glucose_now = st.number_input("æœ€è¿‘è¡€ç³– mg/dL", min_value=30, max_value=600, value=latest_glucose, step=1)
    with col4:
        systolic = st.number_input("æ”¶ç¼©åŽ‹ mmHg", min_value=70, max_value=260, value=130, step=1)
    with col5:
        weight_gain = st.number_input("ä¸¤æ¬¡é€æžé—´ä½“é‡å¢žåŠ  kg", min_value=0.0, max_value=10.0, value=1.0, step=0.1)

    col8, col9 = st.columns(2)
    with col8:
        is_dialysis_day = st.checkbox("ä»Šå¤©æ˜¯é€æžæ—¥", value=default_is_dialysis_day)
    with col9:
        missed_meds = st.number_input(
            "ä»Šå¤©å¿˜è®°è¯ç‰©æ•°é‡",
            min_value=0,
            max_value=20,
            value=today_missed_meds,
            step=1,
            help="å¦‚æžœå·²ç»åœ¨ç”¨è¯æé†’ä¸­æ ‡è®°å¿˜è®°ï¼Œè¿™é‡Œä¼šè‡ªåŠ¨å¸¦å…¥ã€‚",
        )

    section_title("æœ€è¿‘é¥®é£Ÿæƒ…å†µ")
    col10, col11, col12 = st.columns(3)
    with col10:
        salty_food = st.slider("æœ€è¿‘åƒå’¸ç¨‹åº¦", 0, 3, 0, help="é…±æ²¹ã€å’¸èœã€è…Œåˆ¶å“ã€å¤–å–")
    with col11:
        fluid_extra = st.slider("æ±¤æ°´/é¥®æ°´åå¤š", 0, 3, 0, help="æ°´ã€èŒ¶ã€æ±¤ã€ç²¥æ°´éƒ½ç®—")
    with col12:
        sweet_food = st.slider("ç”œé£Ÿæˆ–ä¸»é£Ÿåå¤š", 0, 3, 0, help="ç³–ã€ç”œé¥®æ–™ã€ç±³é¥­ã€é¢ã€ç²¥")

    if st.button("âœ… åˆ†æžæœ¬æ¬¡çŠ¶æ€"):
        if image is None:
            st.html('<div class="alert-red">âš ï¸ è¯·å…ˆæ‹ç…§æˆ–ä¸Šä¼ ç…§ç‰‡ã€‚</div>')
            return

        metrics = face_photo_metrics(image)
        baseline_metrics = (
            face_photo_metrics(st.session_state.face_baseline)
            if st.session_state.face_baseline is not None
            else None
        )

        previous_score = (
            st.session_state.face_history[-1]["score"]
            if st.session_state.face_history
            else None
        )
        assessment = build_ai_support_assessment(
            metrics=metrics,
            baseline_metrics=baseline_metrics,
            symptoms={
                "swelling": swelling,
                "tired": tired,
                "appetite": appetite,
                "breath": breath,
                "dizziness": dizziness,
                "nausea": nausea,
                "edema": edema,
                "confusion": confusion,
            },
            glucose_now=glucose_now,
            systolic=systolic,
            weight_gain=weight_gain,
            is_dialysis_day=is_dialysis_day,
            missed_meds=missed_meds,
            salty_food=salty_food,
            fluid_extra=fluid_extra,
            sweet_food=sweet_food,
            previous_score=previous_score,
        )

        score = assessment["score"]
        level = assessment["level"]
        color = assessment["color"]
        trend = assessment["trend"]

        st.session_state.face_history.append(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "score": score,
                "level": level,
                "trend": trend,
                "glucose": glucose_now,
                "blood_pressure": systolic,
                "weight_gain": weight_gain,
                "missed_meds": missed_meds,
                "dialysis_day": "æ˜¯" if is_dialysis_day else "å¦",
            }
        )

        st.html(
            f"""
            <div class="card" style="border-color:{color};">
                <div class="card-title" style="color:{color};">è¯„åˆ†ï¼š{score}/100 Â· {escape(level)}</div>
                <div class="big-text"><b>è¯„åˆ†ç»„æˆï¼š</b>è§„åˆ™è¯„åˆ† {assessment["rule_score"]}/100ï¼ŒAIæ¨¡åž‹è¯„åˆ† {assessment["ai_score"]}/100ï¼ˆ{escape(assessment["ai_level"])}ï¼‰ã€‚</div>
                <div class="big-text"><b>è¶‹åŠ¿ï¼š</b>{escape(trend)}</div>
                <div class="big-text"><b>æ€»ä½“è¯´æ˜Žï¼š</b>{escape(assessment["summary"])}</div>
                <div class="big-text"><b>ç…§ç‰‡è´¨é‡ï¼š</b>{escape(metrics["quality"])}</div>
                <div class="big-text"><b>ç…§ç‰‡è¯´æ˜Žï¼š</b>{escape(" ".join(assessment["photo_notes"]))}</div>
                <div class="big-text"><b>ä¸»è¦å»ºè®®ï¼š</b>{escape(assessment["recommendation"])}</div>
                <div class="big-text muted"><b>æ¨¡åž‹ï¼š</b>{escape(assessment["model_name"])}ï¼Œè®­ç»ƒæŸå¤± {assessment["model_loss"]}</div>
            </div>
            """
        )

        if assessment["factors"]:
            section_title("é£Žé™©å› ç´ æ˜Žç»†")
            st.dataframe(pd.DataFrame(assessment["factors"]), use_container_width=True, hide_index=True)

            top_advice = "".join(
                f"<li><b>{escape(item['é¡¹ç›®'])}ï¼š</b>{escape(item['å»ºè®®'])}</li>"
                for item in assessment["top_factors"]
            )
            st.html(
                f"""
                <div class="card">
                    <div class="card-title">ä¼˜å…ˆå¤„ç†</div>
                    <ul class="simple-list">{top_advice}</ul>
                </div>
                """
            )
        else:
            st.html('<div class="alert-green">âœ… æ²¡æœ‰æ˜Žæ˜¾é£Žé™©å› ç´ ã€‚è¯·ç»§ç»­æ—¥å¸¸è®°å½•ã€‚</div>')

        if score >= 45:
            st.html(
                """
                <div class="alert-red">
                ðŸš¨ å¦‚æžœå‡ºçŽ°èƒ¸ç—›ã€å‘¼å¸å›°éš¾ã€æ„è¯†ä¸æ¸…ã€ä¸¥é‡ä½Žè¡€ç³–ã€ä¸¥é‡é«˜è¡€åŽ‹ã€é€æžåŽæ˜Žæ˜¾ä¸é€‚ï¼Œè¯·ç«‹å³è”ç³»åŒ»ç”Ÿã€é€æžä¸­å¿ƒæˆ–æ€¥æ•‘ã€‚
                </div>
                """
            )
            if st.session_state.hospital_phone.strip():
                phone = escape(st.session_state.hospital_phone.strip())
                st.html(
                    f"""
                    <a href="tel:{phone}" style="display:inline-block;font-size:24px;font-weight:900;color:white;background:#c62845;padding:14px 18px;border-radius:8px;text-decoration:none;">
                    â˜Žï¸ ç‚¹å‡»æ‹¨æ‰“ï¼š{phone}
                    </a>
                    """
                )

    col6, col7 = st.columns(2)
    with col6:
        if st.button("ðŸ“Œ å°†æœ¬æ¬¡ç…§ç‰‡è®¾ä¸ºåŸºå‡†ç…§ç‰‡"):
            if image is None:
                st.html('<div class="alert-red">âš ï¸ è¯·å…ˆæ‹ç…§æˆ–ä¸Šä¼ ç…§ç‰‡ã€‚</div>')
            else:
                st.session_state.face_baseline = image.copy()
                st.html('<div class="alert-green">âœ… å·²ä¿å­˜ä¸ºåŸºå‡†ç…§ç‰‡ã€‚ä»¥åŽä¼šå’Œè¿™å¼ ç…§ç‰‡æ¯”è¾ƒã€‚</div>')
    with col7:
        if st.button("ðŸ§¹ æ¸…é™¤é¢éƒ¨è§‚å¯ŸåŽ†å²"):
            st.session_state.face_history = []
            st.html('<div class="alert-green">âœ… å·²æ¸…é™¤åŽ†å²è®°å½•ã€‚</div>')

    if st.session_state.face_history:
        section_title("è§‚å¯ŸåŽ†å²")
        st.dataframe(pd.DataFrame(st.session_state.face_history).tail(10), use_container_width=True, hide_index=True)


def main() -> None:
    setup_state()
    inject_style()
    module_options = ["é¦–é¡µ", "é¥®é£ŸåŠ©æ‰‹", "è¿åŠ¨è®¡åˆ’", "è¡€ç³–è®°å½•", "ç”¨è¯æé†’", "AIå¥åº·è§‚å¯Ÿ"]
    if st.session_state.current_module not in module_options:
        st.session_state.current_module = "é¦–é¡µ"
    module = st.session_state.current_module

    with st.sidebar:
        st.html(
            """
            <div style="font-size:30px;font-weight:900;color:#008f5f;line-height:1.25;margin:8px 0 18px;">
            ðŸ’š ç³–å°¿ç—…è‚¾ç—…<br>ç…§æŠ¤åŠ©æ‰‹
            </div>
            """
        )
        st.html(
            """
            <div style="font-size:18px;line-height:1.6;color:#a9b0be;margin-top:24px;">
            é¦–é¡µæ˜¯ä¸»èœå•<br>
            ç‚¹å‡»å¤§æŒ‰é’®è¿›å…¥åŠŸèƒ½<br>
            æ¯ä¸ªé¡µé¢éƒ½èƒ½è¿”å›žé¦–é¡µ
            </div>
            """
        )

    if module == "é¦–é¡µ":
        home_module()
    elif module == "é¥®é£ŸåŠ©æ‰‹":
        diet_module()
    elif module == "è¿åŠ¨è®¡åˆ’":
        exercise_module()
    elif module == "è¡€ç³–è®°å½•":
        glucose_module()
    elif module == "ç”¨è¯æé†’":
        medication_module()
    else:
        face_observation_module()


if __name__ == "__main__":
    main()
