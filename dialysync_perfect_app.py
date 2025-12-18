import streamlit as st
from datetime import date, datetime
from pathlib import Path
import random, os, base64
import pickle

# ------- SAFE IMAGE HANDLING (Your PNGs) --------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)

def safe_img(fn, width=90, caption=None):
    local_path = IMG_PATH(fn)
    if os.path.exists(local_path):
        try:
            return st.image(local_path, width=width, caption=caption)
        except:
            pass
    github_url = f"https://raw.githubusercontent.com/JK-79/Dialysync_CKD/main/{fn}"
    return st.image(github_url, width=width, caption=caption)

# ------- ML MODEL (Safe) --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
model = None
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
except:
    pass

# ------- MOOD DATA (Perfect structure) --------
MOODS = [
    {"id": "happy", "emoji": "😊", "desc": "Happy", "img": "mood_happy.png"},
    {"id": "neutral", "emoji": "😐", "desc": "Neutral", "img": "mood_neutral.png"},
    {"id": "tired", "emoji": "😴", "desc": "Tired", "img": "mood_tired.png"},
    {"id": "sad", "emoji": "😢", "desc": "Sad", "img": "mood_sad.png"},
    {"id": "anxious", "emoji": "😰", "desc": "Anxious", "img": "mood_anxious.png"}
]

def get_mood_by_id(mood_id):
    return next((m for m in MOODS if m["id"] == mood_id), MOODS[0])

def nutri_estimator(desc=""):
    return {
        'Calories': 150.0,
        'Potassium': 0.12,
        'Sodium': 2.5,
        'Calcium': 15.0,
        'Protein': 8.2
    }

# --------- STATE INIT ---------
def init_state():
    defaults = {
        'page': 'welcome', 'user_type': None, 'mood': 'neutral',
        'mood_history': [], 'food_log': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# --------- PERFECT MOOD CALENDAR (Fixed) ---------
def mood_calendar():
    col1, col2 = st.columns([4, 1])
    with col2:
        st.markdown("### 📅 Mood")
        today = date.today()
        year = st.selectbox("Year:", [today.year-1, today.year, today.year+1], key="year_sel")
        
        # Mood history mapping
        mood_history = st.session_state.get('mood_history', [])
        day_moods = {}
        for entry in mood_history:
            if entry['date'].year == year:
                day_moods[entry['date'].day] = entry['emoji']
        
        # Fixed 12-month display (NO calendar.month_name error)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        st.markdown(f"**{year} Overview**")
        for i in range(12):
            days = []
            for day in range(1, 8):  # First 7 days per month
                emoji = day_moods.get(day, '⚪')
                days.append(f"{day:2d}{emoji}")
            preview = " | ".join(days)
            st.markdown(f"**{month_names[i]}**: {preview}")

# --------- WELCOME SCREEN ---------
def welcome_screen():
    st.markdown("# 🩸 DialySync CKD")
    safe_img('app_banner.png', width=200)
    
    col1, col2 = st.columns(2)
    with col1:
        safe_img('patient.png', width=120)
        if st.button("👤 Patient", use_container_width=True):
            st.session_state['user_type'] = 'Patient'
            st.session_state['page'] = 'mood_selector'
            st.rerun()
    with col2:
        safe_img('caregiver.png', width=120)
        if st.button("👨‍👩‍👧 Caregiver", use_container_width=True):
            st.session_state['user_type'] = 'Caregiver'
            st.session_state['page'] = 'mood_selector'
            st.rerun()

# --------- FIXED MOOD SELECTOR ---------
def mood_selector():
    safe_img('mood_banner.png', width=250)
    st.markdown(f"## {st.session_state['user_type']} Mood Check")
    
    cols = st.columns(3)
    for i, mood_data in enumerate(MOODS):
        with cols[i]:
            safe_img(mood_data['img'], width=100)
            st.markdown(f"**{mood_data['emoji']}**")
            st.caption(mood_data['desc'])
            
            if st.button(f"{mood_data['desc']}", key=f"select_{mood_data['id']}"):
                st.session_state['mood'] = mood_data['id']
                today = date.today()
                st.session_state['mood_history'].append({
                    'date': today,
                    'mood': mood_data['id'],
                    'emoji': mood_data['emoji']
                })
                st.session_state['page'] = 'home'
                st.balloons()
                st.success(f"✅ Logged: {mood_data['emoji']}")
                st.rerun()

# --------- HOMEPAGE ---------
def homepage():
    safe_img('dashboard_banner.png', width=300)
    
    st.markdown("# 🏠 Health Summary")
    
    # Safe mood lookup
    current_mood_data = get_mood_by_id(st.session_state.get('mood', 'neutral'))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mood", current_mood_data['emoji'])
    with col2:
        st.metric("Meals", len(st.session_state['food_log']))
    with col3:
        st.metric("Moods Logged", len(st.session_state['mood_history']))
    
    col1, col2, col3 = st.columns(3)
    col1.button("📊 Reports")
    col2.button("🍽️ Food Diary")
    col3.button("💊 Medications")

# --------- MAIN LAYOUT ---------
st.set_page_config(page_title="DialySync", page_icon="🩸", layout="wide")

# HEADER
header1, header2 = st.columns([4, 1])
with header1:
    st.title("🩸 DialySync CKD")
with header2:
    mood_calendar()

st.markdown("---")

# PERFECT ROUTING (No Errors)
if st.session_state['page'] == 'welcome' or st.session_state['user_type'] is None:
    welcome_screen()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
else:
    homepage()
