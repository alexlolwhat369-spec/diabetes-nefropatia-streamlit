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
    page_title="糖尿病肾病照护助手",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


STATUS_META = {
    "eat": {
        "label": "✅ 可以吃",
        "color": "#008f5f",
        "bg": "#e9f8f0",
        "border": "rgba(0, 143, 95, 0.40)",
    },
    "moderate": {
        "label": "⚠️ 适量吃",
        "color": "#a46a00",
        "bg": "#fff8e6",
        "border": "rgba(164, 106, 0, 0.36)",
    },
    "avoid": {
        "label": "❌ 避免",
        "color": "#c62845",
        "bg": "#fff0f3",
        "border": "rgba(198, 40, 69, 0.36)",
    },
}


ASSET_DIR = Path(__file__).parent / "assets"
MEAL_IMAGE = {
    "早餐": ASSET_DIR / "breakfast.png",
    "午餐": ASSET_DIR / "lunch.png",
    "晚餐": ASSET_DIR / "dinner.png",
}


def setup_state() -> None:
    if "glucose_records" not in st.session_state:
        st.session_state.glucose_records = []
    if "medications" not in st.session_state:
        st.session_state.medications = []
    if "med_log" not in st.session_state:
        st.session_state.med_log = {}
    if "dialysis_days" not in st.session_state:
        st.session_state.dialysis_days = ["周三"]
    if "face_baseline" not in st.session_state:
        st.session_state.face_baseline = None
    if "face_history" not in st.session_state:
        st.session_state.face_history = []
    if "hospital_phone" not in st.session_state:
        st.session_state.hospital_phone = ""
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
            padding: 22px;
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
            font-size: 22px;
            color: #34495e;
            line-height: 1.55;
        }

        .quick-card {
            min-height: 170px;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 3px 12px rgba(23, 32, 42, 0.08);
        }

        .quick-card.primary {
            border-color: rgba(0, 143, 95, 0.32);
            background: #f3fcf7;
        }

        .quick-title {
            font-size: 25px;
            font-weight: 900;
            color: #102030;
            margin-bottom: 6px;
        }

        .quick-desc {
            font-size: 20px;
            color: var(--muted);
            line-height: 1.45;
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
    if st.session_state.get("current_module") != "首页":
        back_col, _ = st.columns([1.2, 4])
        with back_col:
            if st.button("返回首页", key=f"back_{title}", use_container_width=True):
                go_to_module("首页")
    st.html(
        f"""
        <div class="main-title">{escape(title)}</div>
        <div class="subtitle">{escape(subtitle)}</div>
        <div class="notice">⚕️ 本应用只用于日常记录和提醒，不能替代医生、护士或营养师的建议。若出现胸痛、严重低血糖、呼吸困难或透析不适，请立即联系医疗人员。</div>
        """
    )


def section_title(text: str) -> None:
    st.html(f'<div class="card-title" style="margin-top: 18px;">{escape(text)}</div>')


def info_card(title: str, body: str, icon: str = "ℹ️") -> None:
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
            <div class="big-text"><b>建议量：</b>{escape(food["portion"])}</div>
            <div class="big-text"><b>原因：</b>{escape(food["reason"])}</div>
            <div class="big-text muted"><b>提醒：</b>{escape(food["tips"])}</div>
        </div>
        """
    )


def measured_recipe_items(meal: dict) -> list[str]:
    name = meal["name"]
    ingredients_text = " ".join(meal["ingredients"])
    items = []

    if "粥" in name:
        items.append("白米：生米25克，煮成1小碗粥；清水300-350毫升，汤水需计入每日饮水量。")
    elif "米饭" in name or "饭" in name or "盖饭" in name or "饭盒" in name:
        items.append("米饭：熟米饭80-100克，约小半碗；血糖高时减到60-80克。")
    elif "面" in name or "米粉" in name or "粉丝" in name or "汤粉" in name:
        items.append("面/米粉/粉丝：干重30-40克，煮熟后约半碗；汤不要多喝。")
    elif "馒头" in name:
        items.append("馒头：半个小馒头，约30-40克。")
    elif "饺" in name or "馄饨" in name:
        items.append("饺子/馄饨皮：4-6个小份，总量约50-70克；同餐不再加米饭。")
    elif "饼" in name:
        items.append("面粉：25克；清水30-40毫升；做成1张小饼。")
    elif "吐司" in name:
        items.append("无糖吐司：半片到1片，约20-30克。")
    else:
        items.append("主食：如本餐含饭、面或粥，控制在小半碗；如没有主食，可按医嘱加小半碗米饭。")

    if "鱼" in ingredients_text or "鱼" in name:
        items.append("白肉鱼：60-80克，约1个掌心大小，清蒸或水煮。")
    if "鸡" in ingredients_text or "鸡" in name:
        items.append("去皮鸡胸肉：60-80克，约1个掌心大小；早餐可用30-50克。")
    if "蛋清" in ingredients_text or "蛋清" in name:
        items.append("鸡蛋清：1个，约30克；需要更多蛋白时按医嘱可用2个。")
    if "豆腐" in ingredients_text or "豆腐" in name:
        items.append("豆腐：40-60克，小块；血磷高时减少或改用蛋清。")
    if "牛肉" in ingredients_text or "牛肉" in name:
        items.append("瘦牛肉：40-50克，少量即可，不建议天天吃。")
    if "虾仁" in ingredients_text or "虾仁" in name:
        items.append("虾仁：40-50克；尿酸高或医生限制海鲜时不要用。")

    items.append("蔬菜：熟菜80-120克，约半碗；绿叶菜先用500毫升清水焯30-60秒后倒掉水。")
    items.append("食用油：每餐最多1茶匙，约5毫升；早餐可用0-2毫升或不放油。")
    items.append("盐：最好不加；如果必须加，全餐最多1/8茶匙，约0.5-0.7克。")
    items.append("酱油：建议0毫升；如医生允许，最多1/4茶匙，约1毫升，不能再额外加盐。")
    items.append("调味：姜2-3片，葱花3克，醋1茶匙约5毫升，或柠檬汁1茶匙约5毫升。")
    return items


def detailed_recipe_steps(meal: dict) -> list[str]:
    name = meal["name"]
    steps = [
        "洗手20秒，准备干净砧板、刀、锅、量勺和小碗。",
        "先按“详细用量”称好食材：主食小份、蛋白1掌心或指定克数、蔬菜半碗。",
        "蔬菜用清水洗净；绿叶菜用500毫升开水焯30-60秒，捞出后倒掉焯菜水。",
        "锅中最多放1茶匙油，约5毫升；早餐或粥类可以不放油。",
    ]

    if "鱼" in name:
        steps.append("鱼肉60-80克加姜2-3片，蒸8-10分钟或煮到完全变白熟透。")
    elif "鸡" in name:
        steps.append("鸡胸肉60-80克用清水煮或蒸10-15分钟，熟透后切片或撕丝。")
    elif "蛋清" in name:
        steps.append("鸡蛋清1个加温水30毫升，蒸6-8分钟到凝固；不要加入蛋黄。")
    elif "豆腐" in name:
        steps.append("豆腐40-60克切小块，蒸或煮3-5分钟；不要油炸。")
    else:
        steps.append("蛋白类食材按食谱煮熟或蒸熟，不使用腌制品、咸鱼、香肠或高盐酱料。")

    if "粥" in name:
        steps.append("生米25克加清水300-350毫升煮成1小碗粥；不要加糖。")
    elif "饭" in name:
        steps.append("熟米饭称80-100克，放入小碗；先吃菜和蛋白，再吃米饭。")
    elif "面" in name or "米粉" in name or "粉丝" in name:
        steps.append("干面/米粉/粉丝30-40克煮熟后沥水；汤汁最多喝几口，不要喝完。")
    elif "饺" in name or "馄饨" in name:
        steps.append("饺子或馄饨控制4-6个小份，蒸或清煮；不蘸酱油。")
    elif "饼" in name:
        steps.append("面粉25克加水30-40毫升调糊，用不粘锅少油煎成1张小饼。")

    steps.extend(meal["steps"])
    steps.extend(
        [
            "最后调味：优先用葱、姜、醋或柠檬汁；盐最多1/8茶匙，酱油尽量不用。",
            "装盘后检查份量：主食小半碗，蛋白1掌心，蔬菜半碗；不要再加甜饮料、咸菜或浓汤。",
            "如果当天透析、血糖异常或医生有特殊限制，以医生和营养师的建议为准。",
        ]
    )
    return steps


def render_recipe_card(meal: dict) -> None:
    image_path = MEAL_IMAGE.get(meal["time"])
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
                    <div class="meal-time">{escape(meal["time"])} · {escape(meal["style"])}</div>
                    <div class="meal-name">{escape(meal["name"])}</div>
                </div>
            </div>
            <div class="big-text"><b>建议份量：</b>{escape(meal["portion"])}</div>
            <div class="nutrient-row">{nutrients}</div>
            <div class="big-text"><b>详细用量：</b></div>
            <ul class="simple-list">{ingredients}</ul>
            <div class="big-text" style="margin-top:10px;"><b>详细做法：</b></div>
            <ol class="simple-list">{steps}</ol>
            <div class="notice" style="margin-bottom:0;"><b>肾病提醒：</b>{escape(meal["renal_note"])}</div>
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
    breakfast = pick_recipes_for_week(week_start, "早餐")
    lunch = pick_recipes_for_week(week_start, "午餐")
    dinner = pick_recipes_for_week(week_start, "晚餐")

    weekly_plan = []
    for index, day_name in enumerate(WEEK_DAYS):
        plan_date = week_start + timedelta(days=index)
        weekly_plan.append(
            {
                "day": day_name,
                "date": plan_date,
                "theme": "自动生成均衡餐",
                "meals": [breakfast[index], lunch[index], dinner[index]],
            }
        )
    return weekly_plan


def render_meal_plan() -> None:
    section_title("自动生成一周三餐")
    st.html(
        """
        <div class="notice">
        🍽️ 系统会从50个食谱中生成本周三餐。每周会自动换一组，并尽量避开上一周已经用过的食谱。重点是优质蛋白、少量主食、低盐、低钾、低磷和稳定血糖。
        </div>
        """
    )

    reference_day = st.date_input("📅 选择本周任意一天", value=date.today())
    week_start = week_start_for(reference_day)
    iso = week_start.isocalendar()
    weekly_plan = build_generated_meal_plan(reference_day)
    selected_day = st.selectbox(
        "📅 选择一天查看三餐",
        [f"{item['day']} {item['date'].strftime('%m-%d')}" for item in weekly_plan],
    )
    day_plan = weekly_plan[
        [f"{item['day']} {item['date'].strftime('%m-%d')}" for item in weekly_plan].index(selected_day)
    ]

    st.html(
        f"""
        <div class="card" style="border-color:rgba(0,143,95,0.35);">
            <div class="card-title">第 {iso.week} 周 · {week_start.strftime("%Y-%m-%d")} 开始</div>
            <div class="big-text">{escape(day_plan["day"])} 的早餐、午餐和晚餐如下。每餐都尽量使用中式做法，并控制盐、糖、钾和磷。</div>
        </div>
        """
    )

    for meal in day_plan["meals"]:
        render_recipe_card(meal)

    show_week = st.checkbox("🗓️ 显示一周总览")
    if show_week:
        overview_rows = []
        for day in weekly_plan:
            overview_rows.append(
                {
                    "日期": day["day"],
                    "日期数字": day["date"].strftime("%m-%d"),
                    "早餐": day["meals"][0]["name"],
                    "午餐": day["meals"][1]["name"],
                    "晚餐": day["meals"][2]["name"],
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
    page_header("饮食助手", "查看一周三餐食谱，也可以搜索常见中餐食物是否适合。")

    st.html(
        """
        <div class="grid">
            <div class="card"><div class="big-icon">🍌</div><div class="big-text"><b>低钾：</b>避免香蕉、番茄、土豆。</div></div>
            <div class="card"><div class="big-icon">🥛</div><div class="big-text"><b>低磷：</b>少奶制品，避免坚果。</div></div>
            <div class="card"><div class="big-icon">🧂</div><div class="big-text"><b>低钠：</b>酱油、咸菜、腌制品要少。</div></div>
            <div class="card"><div class="big-icon">🩸</div><div class="big-text"><b>控糖：</b>不加糖，白米饭要限量。</div></div>
        </div>
        """
    )

    render_meal_plan()

    section_title("食物搜索")
    query = st.text_input("🔎 输入食物名称", placeholder="例如：米饭、豆腐、酱油、香蕉、青菜")
    results = [food for food in FOOD_DATABASE if food_matches(food, query)]

    if not results:
        info_card("没有找到", "请换一个常见名称搜索，或咨询医生/营养师。", "🔎")
        return

    section_title(f"找到 {len(results)} 个结果")
    for food in results:
        render_food_card(food)


def exercise_module() -> None:
    page_header("运动计划", "选择透析日，自动生成每周安全活动安排。透析当天不安排运动。")

    dialysis_days = st.multiselect(
        "🩺 请选择每周透析日",
        WEEK_DAYS,
        default=st.session_state.dialysis_days,
    )
    st.session_state.dialysis_days = dialysis_days

    boxes = []
    for index, day_name in enumerate(WEEK_DAYS):
        is_dialysis = day_name in dialysis_days
        if is_dialysis:
            class_name = "day-box stop"
            icon = "🛑"
            action = "透析日<br><b>今天不运动</b><br>注意休息"
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

    section_title("安全运动")
    cols = st.columns(2)
    for idx, routine in enumerate(EXERCISE_ROUTINES):
        steps = "".join(f"<li>{escape(step)}</li>" for step in routine["steps"])
        with cols[idx % 2]:
            st.html(
                f"""
                <div class="card">
                    <div class="big-icon">{routine["icon"]}</div>
                    <div class="card-title">{escape(routine["name"])}</div>
                    <div class="big-text"><b>时间：</b>{escape(routine["duration"])}</div>
                    <div class="big-text"><b>强度：</b>{escape(routine["intensity"])}</div>
                    <div class="big-text"><ul>{steps}</ul></div>
                </div>
                """
            )

    st.html(
        """
        <div class="notice">🔔 运动时请保持轻松。若头晕、胸闷、心慌、腿脚疼痛或血糖过低，请马上停止并联系家人或医生。</div>
        """
    )


def glucose_zone(value: float) -> tuple[str, str]:
    if value < 70:
        return "危险：血糖偏低", "red"
    if value <= 140:
        return "正常范围", "green"
    if value <= 180:
        return "注意：血糖偏高", "yellow"
    return "危险：血糖过高", "red"


def glucose_module() -> None:
    page_header("血糖记录", "记录每日血糖，查看最近30天趋势和风险颜色区。")

    with st.form("glucose_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            record_date = st.date_input("📅 日期", value=date.today())
        with col2:
            record_time = st.time_input("🕘 时间", value=datetime.now().time().replace(second=0, microsecond=0))
        with col3:
            value = st.number_input("🩸 血糖 mg/dL", min_value=30, max_value=500, value=120, step=1)

        period = st.selectbox("🍽️ 测量时间", ["空腹", "早餐后", "午餐后", "晚餐后", "睡前", "不确定"])
        note = st.text_area("📝 备注", placeholder="例如：今天透析、吃得较多、感觉头晕")
        submitted = st.form_submit_button("✅ 保存血糖记录")

    if submitted:
        st.session_state.glucose_records.append(
            {
                "日期": record_date.isoformat(),
                "时间": record_time.strftime("%H:%M"),
                "血糖": int(value),
                "测量时间": period,
                "备注": note.strip(),
            }
        )
        zone_text, zone_color = glucose_zone(value)
        if zone_color == "green":
            st.html(f'<div class="alert-green">✅ 已保存：{escape(zone_text)}</div>')
        else:
            st.html(f'<div class="alert-red">⚠️ 已保存：{escape(zone_text)}，请按医生建议处理。</div>')

    records = pd.DataFrame(st.session_state.glucose_records)
    if records.empty:
        info_card("还没有记录", "请先输入今天的血糖。保存后，这里会显示趋势图。", "🩸")
        return

    records["日期时间"] = pd.to_datetime(records["日期"] + " " + records["时间"])
    records = records.sort_values("日期时间")
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    recent = records[records["日期时间"] >= cutoff].copy()

    last_value = float(records.iloc[-1]["血糖"])
    last_text, last_color = glucose_zone(last_value)
    if last_color == "green":
        st.html(f'<div class="alert-green">✅ 最新血糖：{int(last_value)} mg/dL，{escape(last_text)}</div>')
    else:
        st.html(f'<div class="alert-red">🚨 最新血糖：{int(last_value)} mg/dL，{escape(last_text)}</div>')

    fig = go.Figure()
    if not recent.empty:
        x0 = recent["日期时间"].min()
        x1 = recent["日期时间"].max()
        if x0 == x1:
            x0 = x0 - pd.Timedelta(hours=12)
            x1 = x1 + pd.Timedelta(hours=12)

        fig.add_hrect(y0=40, y1=70, fillcolor="rgba(255, 92, 122, 0.18)", line_width=0)
        fig.add_hrect(y0=70, y1=140, fillcolor="rgba(0, 255, 136, 0.16)", line_width=0)
        fig.add_hrect(y0=140, y1=180, fillcolor="rgba(255, 209, 102, 0.18)", line_width=0)
        fig.add_hrect(y0=180, y1=500, fillcolor="rgba(255, 92, 122, 0.18)", line_width=0)
        fig.add_trace(
            go.Scatter(
                x=recent["日期时间"],
                y=recent["血糖"],
                mode="lines+markers",
                line=dict(color="#008f5f", width=4),
                marker=dict(size=12, color="#ffffff", line=dict(color="#008f5f", width=2)),
                text=recent["测量时间"],
                hovertemplate="%{x}<br>血糖：%{y} mg/dL<br>%{text}<extra></extra>",
            )
        )
        fig.update_xaxes(range=[x0, x1])

    fig.update_layout(
        title="最近30天血糖趋势",
        paper_bgcolor="#f7fafc",
        plot_bgcolor="#ffffff",
        font=dict(color="#17202a", size=18),
        height=470,
        margin=dict(l=20, r=20, t=60, b=20),
        yaxis=dict(title="mg/dL", range=[40, 260], gridcolor="rgba(23,32,42,0.12)"),
        xaxis=dict(title="日期", gridcolor="rgba(23,32,42,0.10)"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    section_title("最近30天历史")
    display = recent.sort_values("日期时间", ascending=False)[["日期", "时间", "血糖", "测量时间", "备注"]]
    st.dataframe(display, use_container_width=True, hide_index=True)


def today_key(med_id: int, day: date | None = None) -> str:
    day = day or date.today()
    return f"{day.isoformat()}::{med_id}"


def status_for_med(med_id: int, day: date | None = None) -> str:
    return st.session_state.med_log.get(today_key(med_id, day), "pending")


def status_label(status: str) -> str:
    return {
        "taken": "✅ 已服用",
        "pending": "⏰ 待服用",
        "missed": "❌ 已忘记",
    }.get(status, "⏰ 待服用")


def set_med_status(med_id: int, status: str) -> None:
    st.session_state.med_log[today_key(med_id)] = status


def medication_module() -> None:
    page_header("用药提醒", "添加药物、查看今日清单，并记录本周服药完成情况。")

    with st.form("med_form", clear_on_submit=True):
        section_title("添加药物")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("💊 药物名称", placeholder="例如：降糖药、降压药、磷结合剂")
            dose = st.text_input("📏 剂量", placeholder="例如：1片、5mg")
        with col2:
            frequency = st.text_input("🔁 频率", placeholder="例如：每天、每12小时、透析后、周一三五")
            take_time = st.selectbox("🕘 服药时间", ["早上", "中午", "晚上", "睡前", "透析后"])
        notes = st.text_area("📝 特别说明", placeholder="例如：饭后服用、配温水、不要和某药同服")
        add_med = st.form_submit_button("➕ 添加药物")

    if add_med:
        if name.strip():
            st.session_state.medications.append(
                {
                    "id": time_ns(),
                    "name": name.strip(),
                    "dose": dose.strip() or "按医嘱",
                    "frequency": frequency.strip() or "按医嘱",
                    "time": take_time,
                    "notes": notes.strip(),
                }
            )
            st.html('<div class="alert-green">✅ 药物已添加</div>')
        else:
            st.html('<div class="alert-red">⚠️ 请填写药物名称</div>')

    meds = st.session_state.medications
    if not meds:
        info_card("今日没有药物", "请先添加医生开具的药物。", "💊")
        return

    today_missed = [med for med in meds if status_for_med(med["id"]) == "missed"]
    if today_missed:
        names = "、".join(escape(med["name"]) for med in today_missed)
        st.html(f'<div class="alert-red">🚨 今天有药物标记为忘记：{names}</div>')

    section_title("今日药物")
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
                <div class="big-text"><b>剂量：</b>{escape(med["dose"])}</div>
                <div class="big-text"><b>频率：</b>{escape(med["frequency"])}</div>
                <div class="big-text"><b>时间：</b>{escape(med["time"])}</div>
                <div class="big-text muted"><b>说明：</b>{escape(med["notes"] or "无")}</div>
            </div>
            """
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("✅ 已服用", key=f"taken_{med['id']}"):
                set_med_status(med["id"], "taken")
                st.rerun()
        with b2:
            if st.button("⏰ 待服用", key=f"pending_{med['id']}"):
                set_med_status(med["id"], "pending")
                st.rerun()
        with b3:
            if st.button("❌ 忘记了", key=f"missed_{med['id']}"):
                set_med_status(med["id"], "missed")
                st.rerun()

    section_title("本周服药记录")
    rows = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        statuses = [status_for_med(med["id"], day) for med in meds]
        rows.append(
            {
                "日期": day.strftime("%m-%d"),
                "已服用": statuses.count("taken"),
                "待服用": statuses.count("pending"),
                "忘记": statuses.count("missed"),
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
        return "查看今日三餐计划"


def lobby_reminders() -> list[dict]:
    today_name = WEEK_DAYS[date.today().weekday()]
    is_dialysis = today_name in st.session_state.dialysis_days
    pending_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "pending")
    missed_meds = sum(1 for med in st.session_state.medications if status_for_med(med["id"]) == "missed")

    reminders = [
        {
            "icon": "🍽️",
            "title": "今日饮食",
            "desc": today_meal_names(),
        },
        {
            "icon": "💊",
            "title": "用药提醒",
            "desc": f"待服用 {pending_meds} 个，已忘记 {missed_meds} 个。" if st.session_state.medications else "还没有添加药物。",
        },
    ]

    if is_dialysis:
        reminders.append(
            {
                "icon": "🩺",
                "title": "今天是透析日",
                "desc": "不要安排运动，注意休息，饮食和饮水按医护建议执行。",
            }
        )
    else:
        reminders.append(
            {
                "icon": "🚶",
                "title": "今日运动",
                "desc": "可以选择轻松步行15-20分钟，或做坐姿伸展。",
            }
        )

    if st.session_state.glucose_records:
        latest = st.session_state.glucose_records[-1]
        reminders.append(
            {
                "icon": "🩸",
                "title": "最近血糖",
                "desc": f"{latest.get('血糖', '-') } mg/dL，记得继续记录趋势。",
            }
        )
    else:
        reminders.append(
            {
                "icon": "🩸",
                "title": "血糖记录",
                "desc": "今天还没有血糖记录，建议测量后保存。",
            }
        )

    reminders.append(
        {
            "icon": "📷",
            "title": "AI健康观察",
            "desc": "如感觉脸肿、疲劳、胸闷或状态变差，可以拍照并填写症状。",
        }
    )
    return reminders


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
        note = "透析" if is_dialysis else "轻活动"
        if index == today_index:
            note = f"今天 · {note}"
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
            <div class="lobby-title">💚 今日照护首页</div>
            <div class="lobby-subtitle">大字版、手机友好。先看今天要做什么，再进入饮食、运动、血糖、用药或AI健康观察。</div>
        </div>
        """
    )

    section_title("快速进入")
    cards = [
        ("饮食助手", "🍽️", "查看今日三餐、详细用量和食物安全。"),
        ("运动计划", "🚶", "透析日休息，非透析日做轻松运动。"),
        ("血糖记录", "🩸", "记录血糖，查看趋势和风险颜色。"),
        ("用药提醒", "💊", "查看今日药物，标记已服用或忘记。"),
        ("AI健康观察", "📷", "拍照加症状，生成可解释风险评分。"),
    ]

    for start in range(0, len(cards), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            if start + offset >= len(cards):
                continue
            module_name, icon, desc = cards[start + offset]
            with col:
                st.html(
                    f"""
                    <div class="quick-card {'primary' if module_name == '饮食助手' else ''}">
                        <div class="big-icon">{escape(icon)}</div>
                        <div class="quick-title">{escape(module_name)}</div>
                        <div class="quick-desc">{escape(desc)}</div>
                    </div>
                    """
                )
                if st.button(f"进入 {module_name}", key=f"home_{module_name}", use_container_width=True):
                    go_to_module(module_name)

    section_title("本周日历")
    render_lobby_calendar()

    section_title("今日提醒")
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
    quality = "清楚"
    if brightness < 65:
        quality = "照片偏暗"
    elif brightness > 220:
        quality = "照片过亮"
    elif channel_spread < 22:
        quality = "细节偏少"
    return {
        "brightness": round(brightness, 1),
        "redness": round(redness, 1),
        "quality": quality,
    }


def compare_photo_metrics(current: dict, baseline: dict | None) -> list[str]:
    if not baseline:
        return ["还没有基准照片，本次结果会作为以后比较的参考。"]

    notes = []
    brightness_delta = current["brightness"] - baseline["brightness"]
    redness_delta = current["redness"] - baseline["redness"]

    if abs(brightness_delta) > 28:
        notes.append("照片明暗和基准差异较大，比较结果可能不准确。")
    if redness_delta > 16:
        notes.append("照片颜色比基准更红，可能与光线、皮肤状态或不适有关。")
    elif redness_delta < -16:
        notes.append("照片颜色比基准更淡，可能与光线或面色变化有关。")
    if not notes:
        notes.append("照片颜色和明暗与基准接近。")
    return notes


def risk_level(score: int) -> tuple[str, str, str]:
    if score >= 75:
        return "高风险", "#c62845", "请尽快联系医生、透析中心或家人；若有胸痛、呼吸困难、意识不清，请立即急救。"
    if score >= 45:
        return "需要注意", "#a46a00", "今天需要密切观察，复查血糖、血压和体重，并考虑联系医护人员。"
    return "稳定", "#008f5f", "目前记录看起来较稳定，请继续按计划饮食、用药、透析和记录。"


def add_factor(factors: list[dict], name: str, points: int, description: str, advice: str) -> None:
    if points <= 0:
        return
    factors.append(
        {
            "项目": name,
            "分数": points,
            "说明": description,
            "建议": advice,
        }
    )


def recent_glucose_default() -> int:
    if not st.session_state.glucose_records:
        return 120
    try:
        return int(st.session_state.glucose_records[-1]["血糖"])
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
        "呼吸困难或胸闷",
        symptoms["breath"] * 16,
        f"严重程度：{symptoms['breath']}/3。",
        "如果有明显呼吸困难、胸痛或不能平躺，请立即联系医生或急救。",
    )
    add_factor(
        factors,
        "意识或反应变化",
        symptoms["confusion"] * 18,
        f"严重程度：{symptoms['confusion']}/3。",
        "意识不清、反应明显变慢属于危险信号，应尽快寻求医疗帮助。",
    )
    add_factor(
        factors,
        "脸部或眼皮浮肿",
        symptoms["swelling"] * 9,
        f"严重程度：{symptoms['swelling']}/3。",
        "观察是否水分或盐分过多；记录体重，并告知透析团队。",
    )
    add_factor(
        factors,
        "腿脚水肿",
        symptoms["edema"] * 10,
        f"严重程度：{symptoms['edema']}/3。",
        "抬高双腿，检查体重变化；若越来越肿，请联系透析中心。",
    )
    add_factor(
        factors,
        "头晕或站不稳",
        symptoms["dizziness"] * 8,
        f"严重程度：{symptoms['dizziness']}/3。",
        "先坐下休息，检查血糖和血压；不要独自外出。",
    )
    add_factor(
        factors,
        "恶心或呕吐",
        symptoms["nausea"] * 6,
        f"严重程度：{symptoms['nausea']}/3。",
        "少量进食，记录发生时间；若持续呕吐请联系医生。",
    )
    add_factor(
        factors,
        "明显疲劳",
        symptoms["tired"] * 6,
        f"严重程度：{symptoms['tired']}/3。",
        "减少运动，注意休息；若突然明显加重，需要联系医护人员。",
    )
    add_factor(
        factors,
        "食欲变差",
        symptoms["appetite"] * 4,
        f"严重程度：{symptoms['appetite']}/3。",
        "少量多餐，优先保证医生允许的优质蛋白。",
    )

    if glucose_now < 70:
        glucose_points = 25
        glucose_desc = f"血糖 {glucose_now} mg/dL，低于70。"
        glucose_advice = "按低血糖处理方案处理，并联系家人或医生；严重症状请急救。"
    elif glucose_now > 300:
        glucose_points = 25
        glucose_desc = f"血糖 {glucose_now} mg/dL，明显过高。"
        glucose_advice = "按医生给的高血糖方案处理，补充记录饮食和药物，必要时联系医生。"
    elif glucose_now > 250:
        glucose_points = 18
        glucose_desc = f"血糖 {glucose_now} mg/dL，偏高。"
        glucose_advice = "复查血糖，减少主食和甜食，确认降糖药是否按时使用。"
    elif glucose_now > 180:
        glucose_points = 10
        glucose_desc = f"血糖 {glucose_now} mg/dL，需要注意。"
        glucose_advice = "下一餐减少主食，避免甜饮料，并继续记录。"
    else:
        glucose_points = 0
        glucose_desc = ""
        glucose_advice = ""
    add_factor(factors, "血糖", glucose_points, glucose_desc, glucose_advice)

    if systolic >= 180:
        bp_points = 24
        bp_desc = f"收缩压 {systolic} mmHg，属于危险范围。"
        bp_advice = "安静休息后复测；若仍很高或有胸痛头痛，请立即联系医生。"
    elif systolic >= 160:
        bp_points = 14
        bp_desc = f"收缩压 {systolic} mmHg，偏高。"
        bp_advice = "减少盐分，复测血压，确认降压药是否按时服用。"
    elif systolic <= 90:
        bp_points = 18
        bp_desc = f"收缩压 {systolic} mmHg，偏低。"
        bp_advice = "坐下或躺下休息，避免站立；若头晕明显请联系医护人员。"
    else:
        bp_points = 0
        bp_desc = ""
        bp_advice = ""
    add_factor(factors, "血压", bp_points, bp_desc, bp_advice)

    if weight_gain >= 3.0:
        weight_points = 20
        weight_desc = f"两次透析间增加 {weight_gain:.1f} kg，偏多。"
        weight_advice = "限制盐和液体，尽快告知透析中心。"
    elif weight_gain >= 2.0:
        weight_points = 10
        weight_desc = f"两次透析间增加 {weight_gain:.1f} kg，需要注意。"
        weight_advice = "今天减少咸食和汤水，继续记录体重。"
    else:
        weight_points = 0
        weight_desc = ""
        weight_advice = ""
    add_factor(factors, "透析间体重增加", weight_points, weight_desc, weight_advice)

    add_factor(
        factors,
        "今天是透析日",
        4 if is_dialysis_day else 0,
        "透析日前后身体更容易疲劳或不舒服。",
        "透析日避免运动，按医护建议饮食和饮水。",
    )
    add_factor(
        factors,
        "忘记用药",
        min(18, missed_meds * 9),
        f"今天标记忘记 {missed_meds} 个药物。",
        "不要自行补双倍剂量；按医嘱或联系医生/药师确认。",
    )
    add_factor(
        factors,
        "最近吃咸",
        salty_food * 5,
        f"咸食程度：{salty_food}/3。",
        "减少酱油、咸菜、腌制品；观察口渴、血压和水肿。",
    )
    add_factor(
        factors,
        "液体可能偏多",
        fluid_extra * 6,
        f"饮水/汤/粥/茶偏多程度：{fluid_extra}/3。",
        "汤水、粥水、茶都计入液体；按透析团队给的每日限制执行。",
    )
    add_factor(
        factors,
        "甜食或主食偏多",
        sweet_food * 6,
        f"甜食或主食偏多程度：{sweet_food}/3。",
        "避免糖、甜饮料；米饭、面、粥控制小半碗。",
    )

    if metrics["quality"] != "清楚":
        add_factor(
            factors,
            "照片质量",
            4,
            f"本次照片：{metrics['quality']}。",
            "下次用正面、明亮、同一位置拍照，比较会更可靠。",
        )

    photo_notes = compare_photo_metrics(metrics, baseline_metrics)
    if baseline_metrics:
        redness_delta = metrics["redness"] - baseline_metrics["redness"]
        if abs(redness_delta) > 18:
            add_factor(
                factors,
                "面色变化",
                6,
                "照片颜色和基准照片有明显差异。",
                "先确认光线是否相同；若同时有不适症状，请联系医护人员。",
            )

    rule_score = min(100, sum(item["分数"] for item in factors))
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
            "photo_quality_bad": 1 if metrics["quality"] != "清楚" else 0,
            "face_color_change": 1 if baseline_metrics and abs(metrics["redness"] - baseline_metrics["redness"]) > 18 else 0,
        }
    )
    raw_score = int(round((rule_score * 0.65) + (ai_result["score"] * 0.35)))
    level, color, recommendation = risk_level(raw_score)

    if previous_score is None:
        trend = "第一次记录，暂无趋势比较。"
    elif raw_score <= previous_score - 10:
        trend = "比上次更稳定，可能在改善。"
    elif raw_score >= previous_score + 10:
        trend = "比上次更需要注意，可能在变差。"
    else:
        trend = "和上次接近，变化不明显。"

    top_factors = sorted(factors, key=lambda item: item["分数"], reverse=True)[:5]
    if raw_score >= 75:
        summary = "本次结果提示高风险。请优先处理呼吸、意识、血糖、血压或水肿等危险信号。"
    elif raw_score >= 45:
        summary = "本次结果提示需要注意。建议今天加强观察，并复查血糖、血压和体重。"
    else:
        summary = "本次结果整体较稳定。继续保持饮食、用药、透析和记录。"

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

    st.session_state.hospital_phone = st.text_input(
        "☎️ 医院或透析中心电话（可选）",
        value=st.session_state.hospital_phone,
        placeholder="例如：120 或 医院电话",
    )

    source = st.selectbox("📸 选择照片方式", ["手机/电脑摄像头拍照", "上传照片"])
    if source == "手机/电脑摄像头拍照":
        photo_file = st.camera_input("请正面对着镜头，光线明亮，不戴口罩和墨镜")
    else:
        photo_file = st.file_uploader("上传正面脸部照片", type=["png", "jpg", "jpeg"])

    image = load_face_image(photo_file)
    if image is not None:
        st.image(image, caption="本次照片", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        swelling = st.slider("眼皮或脸部浮肿", 0, 3, 0, help="0没有，3明显")
        tired = st.slider("明显疲劳或精神差", 0, 3, 0)
        appetite = st.slider("食欲变差", 0, 3, 0)
        breath = st.slider("呼吸困难或胸闷", 0, 3, 0)
    with col2:
        dizziness = st.slider("头晕、站不稳", 0, 3, 0)
        nausea = st.slider("恶心、呕吐", 0, 3, 0)
        edema = st.slider("脚踝或腿部水肿", 0, 3, 0)
        confusion = st.slider("反应变慢或意识不清", 0, 3, 0)

    section_title("基础数据")
    latest_glucose = recent_glucose_default()
    today_name = WEEK_DAYS[date.today().weekday()]
    default_is_dialysis_day = today_name in st.session_state.dialysis_days
    today_missed_meds = missed_med_count_today()

    col3, col4, col5 = st.columns(3)
    with col3:
        glucose_now = st.number_input("最近血糖 mg/dL", min_value=30, max_value=600, value=latest_glucose, step=1)
    with col4:
        systolic = st.number_input("收缩压 mmHg", min_value=70, max_value=260, value=130, step=1)
    with col5:
        weight_gain = st.number_input("两次透析间体重增加 kg", min_value=0.0, max_value=10.0, value=1.0, step=0.1)

    col8, col9 = st.columns(2)
    with col8:
        is_dialysis_day = st.checkbox("今天是透析日", value=default_is_dialysis_day)
    with col9:
        missed_meds = st.number_input(
            "今天忘记药物数量",
            min_value=0,
            max_value=20,
            value=today_missed_meds,
            step=1,
            help="如果已经在用药提醒中标记忘记，这里会自动带入。",
        )

    section_title("最近饮食情况")
    col10, col11, col12 = st.columns(3)
    with col10:
        salty_food = st.slider("最近吃咸程度", 0, 3, 0, help="酱油、咸菜、腌制品、外卖")
    with col11:
        fluid_extra = st.slider("汤水/饮水偏多", 0, 3, 0, help="水、茶、汤、粥水都算")
    with col12:
        sweet_food = st.slider("甜食或主食偏多", 0, 3, 0, help="糖、甜饮料、米饭、面、粥")

    if st.button("✅ 分析本次状态"):
        if image is None:
            st.html('<div class="alert-red">⚠️ 请先拍照或上传照片。</div>')
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
                "dialysis_day": "是" if is_dialysis_day else "否",
            }
        )

        st.html(
            f"""
            <div class="card" style="border-color:{color};">
                <div class="card-title" style="color:{color};">评分：{score}/100 · {escape(level)}</div>
                <div class="big-text"><b>评分组成：</b>规则评分 {assessment["rule_score"]}/100，AI模型评分 {assessment["ai_score"]}/100（{escape(assessment["ai_level"])}）。</div>
                <div class="big-text"><b>趋势：</b>{escape(trend)}</div>
                <div class="big-text"><b>总体说明：</b>{escape(assessment["summary"])}</div>
                <div class="big-text"><b>照片质量：</b>{escape(metrics["quality"])}</div>
                <div class="big-text"><b>照片说明：</b>{escape(" ".join(assessment["photo_notes"]))}</div>
                <div class="big-text"><b>主要建议：</b>{escape(assessment["recommendation"])}</div>
                <div class="big-text muted"><b>模型：</b>{escape(assessment["model_name"])}，训练损失 {assessment["model_loss"]}</div>
            </div>
            """
        )

        if assessment["factors"]:
            section_title("风险因素明细")
            st.dataframe(pd.DataFrame(assessment["factors"]), use_container_width=True, hide_index=True)

            top_advice = "".join(
                f"<li><b>{escape(item['项目'])}：</b>{escape(item['建议'])}</li>"
                for item in assessment["top_factors"]
            )
            st.html(
                f"""
                <div class="card">
                    <div class="card-title">优先处理</div>
                    <ul class="simple-list">{top_advice}</ul>
                </div>
                """
            )
        else:
            st.html('<div class="alert-green">✅ 没有明显风险因素。请继续日常记录。</div>')

        if score >= 45:
            st.html(
                """
                <div class="alert-red">
                🚨 如果出现胸痛、呼吸困难、意识不清、严重低血糖、严重高血压、透析后明显不适，请立即联系医生、透析中心或急救。
                </div>
                """
            )
            if st.session_state.hospital_phone.strip():
                phone = escape(st.session_state.hospital_phone.strip())
                st.html(
                    f"""
                    <a href="tel:{phone}" style="display:inline-block;font-size:24px;font-weight:900;color:white;background:#c62845;padding:14px 18px;border-radius:8px;text-decoration:none;">
                    ☎️ 点击拨打：{phone}
                    </a>
                    """
                )

    col6, col7 = st.columns(2)
    with col6:
        if st.button("📌 将本次照片设为基准照片"):
            if image is None:
                st.html('<div class="alert-red">⚠️ 请先拍照或上传照片。</div>')
            else:
                st.session_state.face_baseline = image.copy()
                st.html('<div class="alert-green">✅ 已保存为基准照片。以后会和这张照片比较。</div>')
    with col7:
        if st.button("🧹 清除面部观察历史"):
            st.session_state.face_history = []
            st.html('<div class="alert-green">✅ 已清除历史记录。</div>')

    if st.session_state.face_history:
        section_title("观察历史")
        st.dataframe(pd.DataFrame(st.session_state.face_history).tail(10), use_container_width=True, hide_index=True)


def main() -> None:
    setup_state()
    inject_style()
    module_options = ["首页", "饮食助手", "运动计划", "血糖记录", "用药提醒", "AI健康观察"]
    if st.session_state.current_module not in module_options:
        st.session_state.current_module = "首页"
    module = st.session_state.current_module

    with st.sidebar:
        st.html(
            """
            <div style="font-size:30px;font-weight:900;color:#008f5f;line-height:1.25;margin:8px 0 18px;">
            💚 糖尿病肾病<br>照护助手
            </div>
            """
        )
        st.html(
            """
            <div style="font-size:18px;line-height:1.6;color:#a9b0be;margin-top:24px;">
            大字版界面<br>
            明亮背景<br>
            简单提醒
            </div>
            """
        )
        if module != "首页":
            st.html(
                f"""
                <div style="font-size:20px;font-weight:800;color:#34495e;margin-top:24px;">
                当前页面<br>{escape(module)}
                </div>
                """
            )
            if st.button("返回首页", key="sidebar_back_home", use_container_width=True):
                go_to_module("首页")

    if module == "首页":
        home_module()
    elif module == "饮食助手":
        diet_module()
    elif module == "运动计划":
        exercise_module()
    elif module == "血糖记录":
        glucose_module()
    elif module == "用药提醒":
        medication_module()
    else:
        face_observation_module()


if __name__ == "__main__":
    main()
