import streamlit as st
from datetime import date
from pathlib import Path
import pickle, os

# ---------- Image helpers ----------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)

def safe_img(fn, width=90, caption=None):
    local_path = IMG_PATH(fn)
    if os.path.exists(local_path):
        try:
            return st.image(local_path, width=width, caption=caption)
        except:
            pass
    url = f"https://raw.githubusercontent.com/JK-79/Dialysync_CKD/main/{fn}"
    return st.image(url, width=width, caption=caption)

# ---------- (optional) ML model ----------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
model = None
try:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
except Exception:
    model = None

# ---------- Mood config ----------
MOODS = [
    {"id": "happy",   "emoji": "😊", "desc": "Happy",   "img": "mood_happy.png"},
    {"id": "neutral", "emoji": "😐", "desc": "Neutral", "img": "mood_neutral.png"},
    {"id": "tired",   "emoji": "😴", "desc": "Tired",   "img": "mood_tired.png"},
    {"id": "sad",     "emoji": "😢", "desc": "Sad",     "img": "mood_sad.png"},
    {"id": "anxious", "emoji": "😰", "desc": "Anxious", "img": "mood_anxious.png"},
]

def get_mood_by_id(mood_id):
    return next((m for m in MOODS if m["id"] == mood_id), MOODS[1])  # neutral default

# ---------- State ----------
def init_state():
    defaults = {
        "page": "welcome",
        "user_type": None,
        "mood": "neutral",
        "mood_history": [],   # list of {"date": date, "mood": id, "emoji": str}
        "food_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------- Mood calendar (emoji from history) ----------
def mood_calendar():
    st.markdown("## 📅 Mood Calendar")
    today = date.today()
    year = st.selectbox("Year:", [today.year - 1, today.year, today.year + 1], key="year_sel")

    # build map (year, month, day) -> emoji actually logged
    mood_map = {}
    for entry in st.session_state["mood_history"]:
        d = entry["date"]
        if d.year == year:
            mood_map[(d.year, d.month, d.day)] = entry["emoji"]

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # 3 months per row
    for row_start in range(0, 12, 3):
        cols = st.columns(3)
        for i in range(3):
            m_idx = row_start + i
            if m_idx >= 12:
                break
            with cols[i]:
                st.markdown(f"**{month_names[m_idx]} {year}**")
                lines = []
                for day in range(1, 11):  # preview first 10 days
                    try:
                        _ = date(year, m_idx + 1, day)
                        emoji = mood_map.get((year, m_idx + 1, day), "⚪")
                        lines.append(f"{day}: {emoji}")
                    except ValueError:
                        pass
                st.markdown("<br>".join(lines), unsafe_allow_html=True)

# ---------- Screens ----------
def welcome_screen():
    st.markdown("# 🩸 DialySync CKD")
    safe_img("app_banner.png", width=220)

    st.markdown("### Who is using the app?")
    c1, c2 = st.columns(2)
    with c1:
        safe_img("patient.png", width=120)
        if st.button("I am a Patient", use_container_width=True):
            st.session_state["user_type"] = "Patient"
            st.session_state["page"] = "mood_selector"
    with c2:
        safe_img("caregiver.png", width=120)
        if st.button("I am a Caregiver", use_container_width=True):
            st.session_state["user_type"] = "Caregiver"
            st.session_state["page"] = "mood_selector"

def mood_selector():
    st.markdown(f"## {st.session_state['user_type']} – how do you feel today?")
    safe_img("mood_banner.png", width=260)

    cols = st.columns(3)
    for i, m in enumerate(MOODS):
        with cols[i % 3]:
            safe_img(m["img"], width=90)
            st.markdown(f"### {m['emoji']}")
            st.caption(m["desc"])
            if st.button(f"Select {m['desc']}", key=f"mood_{m['id']}", use_container_width=True):
                st.session_state["mood"] = m["id"]
                st.session_state["mood_history"].append(
                    {"date": date.today(), "mood": m["id"], "emoji": m["emoji"]}
                )
                st.session_state["page"] = "home"

def homepage():
    st.markdown("## 🏠 Your CKD overview")
    safe_img("dashboard_banner.png", width=280)

    current = get_mood_by_id(st.session_state["mood"])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Mood today", current["emoji"])
    with c2:
        st.metric("Moods logged", len(st.session_state["mood_history"]))
    with c3:
        st.metric("Meals logged", len(st.session_state["food_log"]))

    st.markdown("### Quick access")
    c1, c2, c3 = st.columns(3)
    c1.button("📊 Reports", use_container_width=True)
    c2.button("🍽️ Food diary", use_container_width=True)
    c3.button("💊 Medications", use_container_width=True)

# ---------- Layout & routing ----------
st.set_page_config(page_title="DialySync CKD", page_icon="🩸", layout="wide")

st.title("🩸 DialySync CKD")
mood_calendar()
st.markdown("---")

if st.session_state["page"] == "welcome" or st.session_state["user_type"] is None:
    welcome_screen()
elif st.session_state["page"] == "mood_selector":
    mood_selector()
else:
    homepage()
