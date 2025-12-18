# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 05:33:44 2025

@author: Jayyant Kakkar
"""

import streamlit as st
import pickle
from pathlib import Path
from PIL import Image
from datetime import datetime, timedelta, date
import random, os, base64
import calendar

# ------- ENHANCED IMAGE HANDLING (Your existing PNGs + GitHub fallback) --------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)

def safe_img(fn, width=90, caption=None, **kwargs):
    """Load from local PNGs first, then GitHub raw URL fallback"""
    local_path = IMG_PATH(fn)
    if os.path.exists(local_path):
        try:
            return st.image(local_path, width=width, caption=caption, **kwargs)
        except:
            pass
    
    # GitHub raw URL fallback for your repo
    github_url = f"https://raw.githubusercontent.com/JK-79/Dialysync_CKD/main/{fn}"
    return st.image(github_url, width=width, caption=caption, **kwargs)

def section_bg(bg_file, opacity=0.65):
    """Light, readable section backgrounds using your PNGs"""
    local_path = IMG_PATH(bg_file)
    if os.path.exists(local_path):
        try:
            with open(local_path, "rb") as f:
                img_data = f.read()
                b64 = base64.b64encode(img_data).decode()
                st.markdown(f"""
                    <style>
                    .main .block-container {{
                        background-image: url('data:image/png;base64,{b64}');
                        background-size: cover;
                        background-repeat: no-repeat;
                        background-position: center;
                        background-opacity: {opacity};
                        padding: 2rem;
                        border-radius: 15px;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
        except:
            pass

# ------- ML MODEL LOADING --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    else:
        model = None
except Exception as e:
    model = None
    st.warning(f"ML model not available: {e}")

# ------- APP CONFIG & DATA --------
MOODS = [
    ("happy", "😊", "Feeling happy", "mood_happy.png"),
    ("neutral", "😐", "Just okay", "mood_neutral.png"),
    ("tired", "😴", "Tired/exhausted", "mood_tired.png"),
    ("sad", "😢", "Sad/down", "mood_sad.png"),
    ("anxious", "😰", "Anxious/worried", "mood_anxious.png")
]

GROCERY = [
    ("Potatoes", "potato.png", "Soak/double-boil to reduce potassium"),
    ("Pudhina (mint)", "pudhina.png", "Flavorful, low potassium"),
    ("Carrots", "carrot.png", "Enjoy sparingly"),
    ("Oats", "oats.png", "Low sodium breakfast option"),
    ("Wheat flour", "wheat.png", "Healthy chapati base")
]

NUTRIT_DICT = {
    'rice': (150, 0.025, 1.1, 4, 3), 'dal': (110, 0.26, 4, 11, 8),
    'roti': (90, 0.08, 3, 5, 2.5), 'potato': (130, 0.42, 7, 7, 2),
    'carrots': (45, 0.32, 4, 3, 1), 'oats': (150, 0.14, 2, 20, 5)
}
LOW_POTASSIUM = ["Apples", "Cabbage", "Berries", "Pineapple", "Rice"]
HIGH_POTASSIUM = ["Bananas", "Potatoes", "Carrots", "Oranges", "Tomatoes"]

def nutri_estimator(desc):
    d = desc.lower().replace(",", " ").split()
    summary = [0, 0, 0, 0, 0]
    for word in d:
        for k in NUTRIT_DICT:
            if k in word:
                v = NUTRIT_DICT[k]
                summary = [x + y for x, y in zip(summary, v)]
    if sum(summary) == 0:
        summary = [random.randint(80, 170), random.uniform(0.01, 0.16), random.uniform(1, 6), random.uniform(4, 19), random.uniform(1, 6)]
    return {
        'Calories': round(summary[0], 1),
        'Potassium (g)': round(summary[1], 2),
        'Sodium (mg)': round(summary[2], 1),
        'Calcium (mg)': round(summary[3], 1),
        'Proteins (g)': round(summary[4], 1),
    }

def mood_chat_response(mood_idx, msg):
    moodsugg = {
        0: "Wonderful! Keep a gratitude journal. 😊",
        1: "Even neutral days need self-care.",
        2: "Deep breaths or a small stretch helps.",
        3: "It's okay to feel down. Connect with loved ones.",
        4: "Practice 4-4-4 breathing. You're not alone."
    }
    return moodsugg.get(mood_idx, "Thank you for sharing!") + "\n💡 Tip: Regular meals support wellbeing."

# --------- STATE INITIALIZATION ---------
def state_init():
    defaults = {
        'page': 'home', 'user_type': None, 'mood': None, 'mood_idx': 0,
        'chat': [], 'food_log': [], 'appoint_date': None, 'mood_history': [],
        'expenditure': 2500, 'appointments': [], 'user_reports': []
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
state_init()

# --------- MOOD CALENDAR (Top Right) ---------
@st.cache_data
def mood_calendar():
    col1, col2 = st.columns([4, 1])
    with col2:
        st.markdown("### 📅 Mood Calendar")
        today = date.today()
        year = st.selectbox("Year", [today.year-1, today.year, today.year+1], key="cal_year")
        
        # Simple mood calendar display
        mood_history = st.session_state.get('mood_history', [])
        cal_data = {d['date']: d['emoji'] for d in mood_history}
        
        st.markdown(f"**{year} Mood Overview**")
        for month in range(1, 13, 3):
            st.markdown(f"**{calendar.month_name[month]}**")
            days = [f"{day:2d}:{cal_data.get(date(year, month, day), '⚪')}" 
                   for day in range(1, 29)]
            st.markdown(" | ".join(days[:7]))

# --------- HOMEPAGE SUMMARY (New Feature) ---------
def homepage():
    section_bg('bg_dashboard.png', 0.6)
    safe_img('dashboard_banner.png', use_container_width=True)
    
    st.markdown("# 🏠 DialySync CKD Dashboard")
    st.markdown("### Welcome back! Here's your complete health overview:")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_mood = dict(MOODS)[st.session_state.get('mood', 'neutral')]
        st.metric("Current Mood", current_mood[1], "😊")
    with col2:
        st.metric("Total Expenditure", f"₹{st.session_state['expenditure']:,}", "₹500")
    with col3:
        st.metric("Appointments", len(st.session_state['appointments']), "+1")
    with col4:
        st.metric("Meals Logged", len(st.session_state['food_log']), "+2")
    
    # Quick access cards
    st.markdown("### 🔍 Quick Access")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        safe_img('reports_icon.png', width=50)
        if st.button("📊 Reports", use_container_width=True):
            st.session_state['page'] = 'reports'
    with col2:
        safe_img('diet_icon.png', width=50)
        if st.button("🍽️ Diet Plan", use_container_width=True):
            st.session_state['page'] = 'diet'
    with col3:
        safe_img('meds_icon.png', width=50)
        if st.button("💊 Medications", use_container_width=True):
            st.session_state['page'] = 'medication'
    with col4:
        safe_img('calendar_icon.png', width=50)
        if st.button("📅 Appointments", use_container_width=True):
            st.session_state['page'] = 'appointments'
    
    # Recent activity
    st.markdown("### 📋 Recent Activity")
    if st.session_state['food_log']:
        latest = st.session_state['food_log'][-1]
        st.markdown(f"**🍽️ Latest Meal:** {latest['desc'][:50]}... | {latest['nutr']['Calories']} cal")
    
    if st.session_state['mood_history']:
        recent_mood = st.session_state['mood_history'][-1]
        st.markdown(f"**😊 Latest Mood:** {recent_mood['emoji']} on {recent_mood['date'].strftime('%b %d')}")
    
    st.markdown("---")
    if st.button("➡️ Full Dashboard"):
        st.session_state['page'] = 'dashboard'

# --------- MOOD SELECTOR WITH IMAGES ---------
def mood_selector():
    section_bg('bg_moods.png', 0.65)
    safe_img('mood_banner.png', width=200)
    
    st.markdown(f"## {st.session_state['user_type']} — How are you feeling today?")
    st.write("*Click the mood that matches your day!*")
    
    cols = st.columns(len(MOODS))
    for i, (mood, emoji, desc, img_file) in enumerate(MOODS):
        with cols[i]:
            safe_img(img_file, width=80)
            st.markdown(f"**{emoji} {desc}**")
            if st.button(f"Select {desc}", key=f"mood_{mood}", use_container_width=True):
                st.session_state['mood'] = mood
                st.session_state['mood_idx'] = i
                today = date.today()
                st.session_state['mood_history'].append({
                    'date': today, 'mood': mood, 'emoji': emoji
                })
                st.session_state['page'] = 'home'
                st.rerun()

# --------- ENHANCED DASHBOARD ---------
def dashboard():
    section_bg('bg_dashboard.png', 0.62)
    safe_img('dashboard_icon.png', width=100)
    
    st.markdown(f"# 📊 Complete Health Dashboard")
    
    # Health metrics
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Blood Pressure", "124/82 mmHg", "↓2")
    with col2: st.metric("Weight", "67.5 kg", "↓0.5")
    with col3: st.metric("Glucose", "104 mg/dL", "Stable")
    
    # ML Prediction (if model available)
    if model:
        with st.expander("🔮 AI Risk Prediction", expanded=True):
            section_bg('bg_ml.png', 0.7)
            col1, col2 = st.columns(2)
            with col1:
                bp = st.slider("BP (mmHg)", 90, 180, 124, key="bp_ml")
                age = st.slider("Age", 18, 90, 45, key="age_ml")
            with col2:
                glucose = st.slider("Glucose (mg/dL)", 60, 220, 104, key="gl_ml")
                protein = st.slider("Protein intake (g)", 10, 100, 45, key="prot_ml")
            
            if st.button("🚨 Calculate CKD Risk", use_container_width=True):
                X = [[bp, glucose, age, protein]]
                prob = model.predict_proba(X)[0,1]
                risk_color = "inverse" if prob > 0.7 else "normal"
                st.metric("CKD Progression Risk", f"{prob:.1%}", delta=None, label_visibility="collapsed")
                if prob > 0.7:
                    st.error("⚠️ High risk detected. Consult your doctor immediately!")
                else:
                    st.success("✅ Risk controlled. Continue healthy routines!")

# --------- FOOD DIARY WITH BACKGROUND ---------
def food_diary():
    section_bg('bg_food.png', 0.68)
    safe_img('food_banner.png', width=250)
    
    st.markdown("# 🍽️ Smart Food Diary & Nutrition Tracker")
    
    with st.form("foodlogger", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            meal = st.text_area("Describe your meal (e.g., 'dal rice chapati salad')", height=80)
        with col2:
            pic = st.file_uploader("📸 Meal photo", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("✅ Log This Meal", use_container_width=True)
    
    if submitted and meal.strip():
        report = nutri_estimator(meal)
        if pic:
            st.image(pic, width=250, caption="Great job capturing your meal!")
            st.success("🌟 Wow! You're really taking care of yourself! 😊")
        st.markdown("### 📊 Nutrition Analysis")
        col1, col2, col3 = st.columns(3)
        col1.metric("Calories", f"{report['Calories']} kcal")
        col2.metric("Potassium", f"{report['Potassium (g)']}g")
        col3.metric("Protein", f"{report['Proteins (g)']}g")
        
        st.session_state['food_log'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'desc': meal,
            'img': pic.name if pic else None,
            'nutr': report
        })
        st.balloons()

# --------- DIET & GROCERY WITH IMAGES ---------
def diet():
    section_bg('bg_diet.png', 0.67)
    safe_img('diet_banner.png', width=200)
    
    st.markdown("# 🥗 Renal Diet & Grocery Guide")
    
    # Grocery list with icons
    st.markdown("### 🛒 Weekly Grocery List")
    cols = st.columns(len(GROCERY))
    for i, (food, icon, tip) in enumerate(GROCERY):
        with cols[i]:
            safe_img(icon, width=60)
            st.markdown(f"**{food}**")
            st.caption(tip)
    
    st.markdown("### ⚠️ Potassium Guide")
    col1, col2 = st.columns(2)
    with col1:
        st.error("**High Potassium (Limit):**")
        for food in HIGH_POTASSIUM:
            st.write(f"• {food}")
    with col2:
        st.success("**Low Potassium (Safe):**")
        for food in LOW_POTASSIUM:
            st.write(f"• {food}")

# --------- MAIN APP LAYOUT ---------
st.set_page_config(
    page_title="DialySync CKD Care", 
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# HEADER WITH MOOD CALENDAR
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    safe_img('app_banner.png', width=120)
    st.markdown("# DialySync CKD Care Platform")
    st.caption("Comprehensive care management for CKD patients & caregivers")
with header_col2:
    mood_calendar()

st.markdown("---")

# MAIN PAGE ROUTING
if st.session_state['page'] == 'home' or st.session_state['user_type'] is None:
    homepage()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
elif st.session_state['page'] == 'dashboard':
    dashboard()
elif st.session_state['page'] == 'food_diary':
    food_diary()
elif st.session_state['page'] == 'diet':
    diet()
else:
    homepage()  # Default fallback
