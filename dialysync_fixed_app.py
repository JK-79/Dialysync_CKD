# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 05:53:40 2025

@author: Jayyant Kakkar
"""

import streamlit as st
import pickle
from pathlib import Path
from PIL import Image
from datetime import datetime, timedelta, date
import random, os, base64
import calendar

# ------- ENHANCED IMAGE HANDLING --------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)

def safe_img(fn, width=90, caption=None, **kwargs):
    local_path = IMG_PATH(fn)
    if os.path.exists(local_path):
        try:
            return st.image(local_path, width=width, caption=caption, **kwargs)
        except:
            pass
    github_url = f"https://raw.githubusercontent.com/JK-79/Dialysync_CKD/main/{fn}"
    return st.image(github_url, width=width, caption=caption, **kwargs)

def section_bg(bg_file, opacity=0.65):
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
                        opacity: {opacity};
                        padding: 2rem;
                        border-radius: 15px;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
        except:
            pass

# ------- ML MODEL (Safe loading) --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
model = None
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
except:
    pass

# ------- APP DATA --------
MOOD_DICT = {
    'happy': ('😊', 'Feeling happy', 'mood_happy.png'),
    'neutral': ('😐', 'Just okay', 'mood_neutral.png'),
    'tired': ('😴', 'Tired', 'mood_tired.png'),
    'sad': ('😢', 'Sad', 'mood_sad.png'),
    'anxious': ('😰', 'Anxious', 'mood_anxious.png')
}

GROCERY = [
    ("Potatoes", "potato.png", "Soak/double-boil"),
    ("Pudhina", "pudhina.png", "Low potassium"),
    ("Carrots", "carrot.png", "Moderation"),
    ("Oats", "oats.png", "Low sodium"),
    ("Wheat flour", "wheat.png", "Chapati base")
]

NUTRIT_DICT = {
    'rice': (150, 0.025, 1.1, 4, 3), 'dal': (110, 0.26, 4, 11, 8),
    'roti': (90, 0.08, 3, 5, 2.5)
}

def nutri_estimator(desc):
    summary = [0, 0, 0, 0, 0]
    if desc:
        d = desc.lower().split()
        for word in d:
            for k, v in NUTRIT_DICT.items():
                if k in word:
                    summary = [x + y for x, y in zip(summary, v)]
    if sum(summary) == 0:
        summary = [120, 0.1, 2, 10, 5]
    return {
        'Calories': round(summary[0], 1),
        'Potassium (g)': round(summary[1], 2),
        'Sodium (mg)': round(summary[2], 1),
        'Calcium (mg)': round(summary[3], 1),
        'Proteins (g)': round(summary[4], 1),
    }

# --------- STATE ---------
def state_init():
    defaults = {
        'page': 'home', 'user_type': None, 'mood': 'neutral',
        'chat': [], 'food_log': [], 'mood_history': [],
        'expenditure': 2500
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
state_init()

# --------- FIXED MOOD CALENDAR (No caching, full width) ---------
def mood_calendar():
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col2:
        st.markdown("### 📅 Mood Calendar")
        today = date.today()
        year = st.selectbox("Select Year:", 
                          [today.year-1, today.year, today.year+1], 
                          key="calendar_year")
        
        # Get mood history for display
        mood_history = st.session_state.get('mood_history', [])
        mood_map = {}
        for entry in mood_history:
            if entry['date'].year == year:
                mood_map[entry['date'].day] = entry['emoji']
        
        # Display 3-month calendar preview
        for month in [1, 4, 7, 10]:
            st.markdown(f"**{calendar.month_name[month]} {year}**")
            days = []
            for day in range(1, 29):
                emoji = mood_map.get(day, '⚪')
                days.append(f"{day:2d}{emoji}")
            st.markdown(" | ".join(days[:7]))
    
    st.markdown("---")

# --------- FIXED HOMEPAGE ---------
def homepage():
    section_bg('bg_dashboard.png', 0.6)
    
    st.markdown("# 🏠 DialySync CKD Dashboard")
    
    # Safe mood display
    current_mood_key = st.session_state.get('mood', 'neutral')
    current_mood = MOOD_DICT.get(current_mood_key, ('😐', 'Neutral', 'neutral.png'))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Mood", current_mood[0])
    with col2:
        st.metric("Total Spend", f"₹{st.session_state['expenditure']:,}")
    with col3:
        st.metric("Meals Logged", len(st.session_state['food_log']))
    
    # Quick access
    col1, col2, col3, col4 = st.columns(4)
    with col1: 
        if st.button("📊 Reports"): st.session_state['page'] = 'reports'
    with col2: 
        if st.button("🍽️ Diet"): st.session_state['page'] = 'diet'
    with col3: 
        if st.button("💊 Meds"): st.session_state['page'] = 'meds'
    with col4: 
        if st.button("📅 Appts"): st.session_state['page'] = 'appts'
    
    st.markdown("### Recent Activity")
    if st.session_state['food_log']:
        latest = st.session_state['food_log'][-1]
        st.write(f"**Meal:** {latest['desc'][:40]}...")

# --------- MOOD SELECTOR ---------
def mood_selector():
    section_bg('bg_moods.png', 0.65)
    st.markdown(f"## {st.session_state['user_type']} — Select Mood")
    
    cols = st.columns(3)
    for i, (mood, emoji, desc, img) in enumerate(MOOD_DICT.items()):
        with cols[i%3]:
            safe_img(img, width=80)
            st.markdown(f"**{emoji}**")
            st.caption(desc)
            if st.button(f"Select {mood}", key=f"moodbtn_{mood}"):
                st.session_state['mood'] = mood
                today = date.today()
                st.session_state['mood_history'].append({
                    'date': today, 'mood': mood, 'emoji': emoji
                })
                st.session_state['page'] = 'home'
                st.success(f"Mood logged: {emoji}")
                st.rerun()

# --------- MAIN LAYOUT ---------
st.set_page_config(page_title="DialySync CKD", layout="wide")

# HEADER
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🩸 DialySync CKD Care")
with col2:
    mood_calendar()

# ROUTING
if st.session_state.get('user_type') is None:
    st.markdown("### Welcome! Are you a...")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 Patient"): 
            st.session_state['user_type'] = 'Patient'
            st.session_state['page'] = 'mood_selector'
            st.rerun()
    with col2:
        if st.button("👨‍👩‍👧 Caregiver"): 
            st.session_state['user_type'] = 'Caregiver'
            st.session_state['page'] = 'mood_selector'
            st.rerun()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
else:
    homepage()
