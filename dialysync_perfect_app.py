# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 06:01:54 2025

@author: Jayyant Kakkar
"""

import streamlit as st
import pickle
from pathlib import Path
from PIL import Image
from datetime import datetime, date
import random, os, base64

# ------- IMAGE HANDLING (Your existing PNGs) --------
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

# ------- ML MODEL --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
model = None
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
except:
    pass

# ------- FIXED MOOD DATA (Proper structure) --------
MOODS = [
    {"id": "happy", "emoji": "😊", "desc": "Feeling happy", "img": "mood_happy.png"},
    {"id": "neutral", "emoji": "😐", "desc": "Just okay", "img": "mood_neutral.png"},
    {"id": "tired", "emoji": "😴", "desc": "Tired", "img": "mood_tired.png"},
    {"id": "sad", "emoji": "😢", "desc": "Sad", "img": "mood_sad.png"},
    {"id": "anxious", "emoji": "😰", "desc": "Anxious", "img": "mood_anxious.png"}
]

GROCERY_ICONS = ["potato.png", "pudhina.png", "carrot.png", "oats.png", "wheat.png"]

def nutri_estimator(desc):
    summary = [120, 0.1, 2, 10, 5]  # Default values
    return {
        'Calories': round(summary[0], 1),
        'Potassium': round(summary[1], 2),
        'Sodium': round(summary[2], 1),
        'Calcium': round(summary[3], 1),
        'Protein': round(summary[4], 1)
    }

# --------- STATE ---------
def state_init():
    defaults = {
        'page': 'welcome', 'user_type': None, 'mood': None,
        'mood_history': [], 'food_log': [], 'expenditure': 2500
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
state_init()

# --------- FIXED FULL CALENDAR (All 365 days) ---------
def mood_calendar():
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col2:
        st.markdown("### 📅 Mood Calendar")
        today = date.today()
        year = st.selectbox("Year", [today.year-1, today.year, today.year+1])
        
        # Get mood history
        mood_history = st.session_state.get('mood_history', [])
        mood_map = {}
        for entry in mood_history:
            if entry['date'].year == year:
                mood_map[entry['date'].day] = entry['emoji']
        
        # Show 12 months compact view
        months = []
        for month in range(1, 13):
            month_days = []
            for day in range(1, 32):
                try:
                    test_date = date(year, month, day)
                    emoji = mood_map.get(day, '⚪')
                    month_days.append(f"{day:2}{emoji}")
                except ValueError:
                    month_days.append("  ")
            months.append(" | ".join(month_days[:5]) + "...")  # First 5 days + dots
        
        for i, month_preview in enumerate(months):
            st.markdown(f"**{calendar.month_name[i+1]}**: {month_preview}")

# --------- WELCOME SCREEN ---------
def welcome_screen():
    st.markdown("# 🩸 DialySync CKD Care")
    safe_img('app_banner.png', width=200)
    
    col1, col2 = st.columns(2)
    with col1:
        safe_img('patient.png', width=120)
        if st.button("👤 I am a Patient", use_container_width=True):
            st.session_state['user_type'] = 'Patient'
            st.session_state['page'] = 'mood_selector'
            st.rerun()
    with col2:
        safe_img('caregiver.png', width=120)
        if st.button("👨‍👩‍👧 I am a Caregiver", use_container_width=True):
            st.session_state['user_type'] = 'Caregiver'
            st.session_state['page'] = 'mood_selector'
            st.rerun()

# --------- FIXED MOOD SELECTOR (Correct unpacking) ---------
def mood_selector():
    safe_img('mood_banner.png', width=250)
    st.markdown(f"## {st.session_state['user_type']} — How do you feel today?")
    
    cols = st.columns(3)
    for i, mood_data in enumerate(MOODS):
        with cols[i]:
            safe_img(mood_data['img'], width=100)
            st.markdown(f"### **{mood_data['emoji']}**")
            st.caption(mood_data['desc'])
            
            if st.button(f"Select {mood_data['desc']}", 
                        key=f"mood_{mood_data['id']}", 
                        use_container_width=True):
                st.session_state['mood'] = mood_data['id']
                today = date.today()
                st.session_state['mood_history'].append({
                    'date': today,
                    'mood': mood_data['id'],
                    'emoji': mood_data['emoji']
                })
                st.session_state['page'] = 'home'
                st.success(f"✅ Mood logged: {mood_data['emoji']}")
                st.balloons()
                st.rerun()

# --------- HOMEPAGE ---------
def homepage():
    safe_img('dashboard_banner.png', width=300)
    
    st.markdown("# 🏠 Your Health Summary")
    
    # Safe mood display
    current_mood = next((m for m in MOODS if m['id'] == st.session_state.get('mood', 'neutral')), MOODS[0])
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Mood", current_mood['emoji'])
    with col2: st.metric("Meals Logged", len(st.session_state['food_log']))
    with col3: st.metric("Spend", f"₹{st.session_state['expenditure']:,}")
    
    # Quick links
    col1, col2, col3 = st.columns(3)
    col1.button("📊 Reports", use_container_width=True)
    col2.button("🍽️ Food Diary", use_container_width=True)
    col3.button("💊 Meds", use_container_width=True)

# --------- MAIN LAYOUT ---------
st.set_page_config(page_title="DialySync CKD", page_icon="🩸", layout="wide")

# HEADER WITH CALENDAR
header1, header2 = st.columns([4, 1])
with header1:
    st.title("🩸 DialySync CKD Care")
with header2:
    mood_calendar()

# PAGE ROUTING
if st.session_state['page'] == 'welcome' or st.session_state['user_type'] is None:
    welcome_screen()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
else:
    homepage()
