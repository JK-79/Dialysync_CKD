# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18 02:50:55 2025

@author: Jayyant Kakkar
"""

import streamlit as st
from PIL import Image
from datetime import datetime, timedelta, date
import random, os, pickle
from pathlib import Path
import calendar

# ------- MODEL LOADING (with error handling) --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    else:
        model = None
except Exception as e:
    model = None

# ------- APP CONFIG ---------
MOODS = [
    ("happy", "😊", "Feeling happy"),
    ("neutral", "😐", "Just okay"),
    ("tired", "😴", "Tired/exhausted"),
    ("sad", "😢", "Sad/down"),
    ("anxious", "😰", "Anxious/worried")
]

GROCERY = [
    ("Potatoes", "Soak/double-boil to reduce potassium"),
    ("Pudhina (mint)", "Flavorful, low potassium"),
    ("Carrots", "Enjoy sparingly"),
    ("Oats", "Low sodium breakfast option"),
    ("Wheat flour", "Healthy chapati base")
]

NUTRIT_DICT = {
    'rice': (150, 0.025, 1.1, 4, 3), 'dal': (110, 0.26, 4, 11, 8),
    'roti': (90, 0.08, 3, 5, 2.5), 'potato': (130, 0.42, 7, 7, 2),
    'carrots': (45, 0.32, 4, 3, 1)
}
LOW_POTASSIUM = ["Apples", "Cabbage", "Berries", "Pineapple", "Rice"]
HIGH_POTASSIUM = ["Bananas", "Potatoes", "Carrots", "Oranges", "Tomatoes"]

# --------- State ---------
def state_init():
    defaults = {
        'page': 'home', 'user_type': None, 'mood': None, 'chat': [],
        'food_log': [], 'appoint_date': None, 'mood_history': [],
        'expenditure': 0, 'appointments': [], 'user_reports': []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
state_init()

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

def mood_chat_response(mood, msg):
    moodsugg = {
        'happy': "Wonderful! Keep a gratitude journal. 😊",
        'neutral': "Even neutral days need self-care.",
        'tired': "Deep breaths or a small stretch helps.",
        'sad': "It's okay to feel down. Connect with loved ones.",
        'anxious': "Practice 4-4-4 breathing. You're not alone."
    }
    return moodsugg.get(mood, "Thank you for sharing!") + "\nTip: Regular meals support wellbeing."

# --------- MOOD CALENDAR COMPONENT ---------
def mood_calendar():
    col1, col2 = st.columns([4, 1])
    with col2:
        st.markdown("### 📅 Mood Calendar")
        today = date.today()
        year = st.selectbox("Year", [today.year-1, today.year, today.year+1], key="cal_year")
        
        # Generate calendar
        cal = calendar.monthcalendar(year, 1)  # January
        st.markdown(f"**{year} Mood Overview**")
        
        for week in cal[:4]:  # Show first 4 weeks
            week_emojis = []
            for day in week:
                if day == 0:
                    week_emojis.append("  ")
                else:
                    date_key = date(year, 1, day)
                    mood_emoji = next((emoji for d, emoji, _ in MOODS if d in st.session_state.get('mood_history', []) and date_key in [dd['date'] for dd in st.session_state['mood_history']]), "⚪")
                    week_emojis.append(mood_emoji)
            st.markdown(" | ".join(week_emojis))

# --------- HOMEPAGE SUMMARY ---------
def homepage():
    st.markdown("# 🏠 CKD Care Dashboard")
    st.markdown("### Welcome back! Here's your health overview:")
    
    # Header with user info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Mood", dict(MOODS)[st.session_state.get('mood', 'neutral')][1], "😊")
    with col2:
        st.metric("Total Expenditure", f"₹{st.session_state['expenditure']:,}", "₹500")
    with col3:
        st.metric("Appointments", len(st.session_state['appointments']), "+1")
    
    # Quick access cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state['page'] = 'reports'
    with col2:
        if st.button("🍽️ Dietary Plan", use_container_width=True):
            st.session_state['page'] = 'diet'
    with col3:
        if st.button("💊 Medications", use_container_width=True):
            st.session_state['page'] = 'medication'
    with col4:
        if st.button("📅 Appointments", use_container_width=True):
            st.session_state['page'] = 'appointments'
    
    # Recent activity
    st.markdown("### Recent Activity")
    if st.session_state['food_log']:
        latest_meal = st.session_state['food_log'][-1]
        st.markdown(f"**Latest Meal:** {latest_meal['desc'][:50]}... | {latest_meal['nutr']['Calories']} cal")
    
    if st.session_state['mood_history']:
        recent_mood = st.session_state['mood_history'][-1]
        st.markdown(f"**Latest Mood:** {recent_mood['mood']} on {recent_mood['date'].strftime('%b %d')}")
    
    st.markdown("---")
    if st.button("➡️ Go to Full Dashboard"):
        st.session_state['page'] = 'dashboard'

# --------- OTHER PAGES (unchanged core functionality) ---------
def mood_selector():
    st.markdown(f"## {st.session_state['user_type']} — Select your mood:")
    cols = st.columns(len(MOODS))
    for i, (mood, emoji, desc) in enumerate(MOODS):
        with cols[i]:
            st.markdown(f"**{emoji}**")
            st.markdown(f"*{desc}*")
            if st.button(desc, key=f"mood_{mood}"):
                st.session_state['mood'] = mood
                # Add to mood history
                today = date.today()
                st.session_state['mood_history'].append({
                    'date': today, 'mood': mood, 'emoji': emoji
                })
                st.session_state['page'] = 'home'
                st.rerun()

def dashboard():
    st.markdown("# 📊 Full Dashboard")
    # ML prediction widget if available
    if model:
        with st.expander("🔮 ML Risk Prediction"):
            col1, col2 = st.columns(2)
            with col1:
                bp = st.slider("BP (mmHg)", 90, 180, 124)
                age = st.slider("Age", 18, 90, 45)
            with col2:
                glucose = st.slider("Glucose (mg/dL)", 60, 220, 104)
                protein = st.slider("Protein (g)", 10, 100, 45)
            if st.button("Calculate Risk"):
                X = [[bp, glucose, age, protein]]
                prob = model.predict_proba(X)[0,1]
                st.metric("CKD Progression Risk", f"{prob:.1%}", "Low")
    
    st.markdown("### Quick Stats")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("BP", "124/82 mmHg")
    with col2: st.metric("Weight", "67.5 kg")
    with col3: st.metric("Glucose", "104 mg/dL")

def food_diary():
    st.markdown("# 🍽️ Food Diary")
    with st.form("foodlog"):
        meal = st.text_area("Describe your meal")
        pic = st.file_uploader("Upload photo")
        if st.form_submit_button("Log Meal"):
            if meal:
                report = nutri_estimator(meal)
                st.session_state['food_log'].append({
                    'time': datetime.now(), 'desc': meal, 'nutr': report
                })
                st.success("Meal logged!")
                st.json(report)

def main_menu():
    st.sidebar.title("Navigation")
    pages = ["Homepage", "Dashboard", "Food Diary", "Diet Plan", "Medications", 
             "Appointments", "Mood Coach", "Doctor Finder"]
    selection = st.sidebar.selectbox("Go to", pages)
    
    if selection == "Homepage":
        homepage()
    elif selection == "Dashboard":
        dashboard()
    elif selection == "Food Diary":
        food_diary()
    # Add other pages...

# --------- MAIN APP ---------
st.set_page_config(page_title="DialySync CKD", layout="wide")

# Header with mood calendar
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("DialySync CKD Care")
with header_col2:
    mood_calendar()

# Main routing
if st.session_state['page'] == 'home' or st.session_state['user_type'] is None:
    homepage()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
else:
    main_menu()
