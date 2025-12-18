import streamlit as st
from datetime import date, datetime
from pathlib import Path
import pickle, os, calendar, random

# ---------- Image helper ----------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)
GITHUB_ROOT = "https://raw.githubusercontent.com/JK-79/Dialysync_CKD/main"

def safe_img(fn, width=90, caption=None):
    local_path = IMG_PATH(fn)
    if os.path.exists(local_path):
        try:
            return st.image(local_path, width=width, caption=caption)
        except Exception:
            pass
    url = f"{GITHUB_ROOT}/{fn}"
    return st.image(url, width=width, caption=caption)

# ---------- Optional ML model ----------
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
    return next((m for m in MOODS if m["id"] == mood_id), MOODS[1])  # default neutral

# ---------- Simple nutrient stub + CKD-aware feedback ----------
HIGH_POTASSIUM_FOODS = [
    "banana", "oranges", "orange juice", "coconut water", "avocado",
    "potato", "sweet potato", "tomato", "tomato juice", "spinach",
    "dried fruits", "dry fruits", "dates"
]

def nutri_estimator(desc: str):
    # Very rough demo numbers, independent of text
    return {
        "Calories": random.randint(120, 280),
        "Potassium (g)": round(random.uniform(0.05, 0.25), 2),
        "Sodium (mg)": random.randint(2, 40),
        "Calcium (mg)": random.randint(5, 80),
        "Protein (g)": round(random.uniform(3, 15), 1)
    }

def ckd_diet_feedback(desc: str, potassium_limit: str, salt_limit_g: float):
    text = desc.lower()
    warnings = []

    # Potassium awareness (rule-of-thumb only)
    if potassium_limit in ["Moderate", "Strict"]:
        if any(food in text for food in HIGH_POTASSIUM_FOODS):
            warnings.append(
                "This meal contains items that are often high in potassium "
                "(e.g. banana, orange juice, coconut water, potatoes, tomatoes, dark greens). "
                "Discuss portion sizes with your dietitian."
            )

    # Sodium awareness (rule-of-thumb only)
    salty_keywords = ["pickle", "papad", "chips", "soup", "sauce", "soy sauce",
                      "maggi", "noodles", "processed", "packet", "ready to eat"]
    if salt_limit_g <= 3.0:
        if any(word in text for word in salty_keywords):
            warnings.append(
                "You selected foods that can be high in salt (pickles, packaged snacks, sauces). "
                "Try to limit added salt and processed foods."
            )

    if not warnings:
        return "Looks generally kidney‑friendly for many patients. Still confirm with your doctor/dietitian."
    return " ".join(warnings)

# ---------- State ----------
def init_state():
    defaults = {
        "page": "welcome",          # welcome, mood, home, diet, food, meds, vitals, doctors
        "user_type": None,
        "mood": "neutral",
        "mood_history": [],         # {"date": date, "mood": id, "emoji": str}
        "food_log": [],             # {"time": str, "desc": str, "nutr": dict}
        "expenditure": 0,

        # Diet profile
        "diet_type": "Vegetarian",
        "salt_limit": 3.0,
        "potassium_limit": "None",
        "fluid_allowance": 1.5,

        # Vitals
        "bp_log": [],               # {"time": str, "sys": int, "dia": int, "hr": int, "urine": int}
        "weight_log": [],           # {"time": str, "weight": float}

        # Medications
        "med_list": [],             # {"name": str, "dose": str, "schedule": str}
        "med_intake": [],           # {"time": str, "name": str, "taken": bool}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------- Mood calendar (full month) ----------
def mood_calendar():
    st.markdown("## 📅 Mood Calendar")
    today = date.today()
    c1, c2 = st.columns(2)
    with c1:
        year = st.selectbox(
            "Year:",
            [today.year - 1, today.year, today.year + 1],
            index=1,
            key="cal_year",
        )
    with c2:
        month = st.selectbox(
            "Month:",
            list(range(1, 13)),
            format_func=lambda m: calendar.month_name[m],
            index=today.month - 1,
            key="cal_month",
        )

    mood_map = {}
    for entry in st.session_state["mood_history"]:
        d = entry["date"]
        mood_map[(d.year, d.month, d.day)] = entry["emoji"]

    st.markdown(f"### {calendar.month_name[month]} {year}")

    week_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, name in enumerate(week_names):
        header_cols[i].markdown(f"**{name}**")

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("&nbsp;", unsafe_allow_html=True)
            else:
                emoji = mood_map.get((year, month, day), "⚪")
                cols[i].markdown(f"{day} {emoji}")

# ---------- Screens ----------
def welcome_screen():
    st.markdown("### Who is using the app?")
    c1, c2 = st.columns(2)
    with c1:
        safe_img("patient.png", width=120)
        if st.button("I am a Patient", use_container_width=True):
            st.session_state["user_type"] = "Patient"
            st.session_state["page"] = "mood"
    with c2:
        safe_img("caregiver.png", width=120)
        if st.button("I am a Caregiver", use_container_width=True):
            st.session_state["user_type"] = "Caregiver"
            st.session_state["page"] = "mood"

def mood_selector():
    st.markdown(f"## {st.session_state['user_type']} – how do you feel today?")
    safe_img("mood_banner.png", width=260)

    selected_date = st.date_input(
        "Select the date you are logging mood for:",
        value=date.today(),
        key="mood_log_date",
    )

    st.markdown("#### Choose your mood:")
    cols = st.columns(3)
    for i, m in enumerate(MOODS):
        with cols[i % 3]:
            safe_img(m["img"], width=90)
            st.markdown(f"### {m['emoji']}")
            st.caption(m["desc"])
            if st.button(
                f"Select {m['desc']}",
                key=f"mood_{m['id']}",
                use_container_width=True,
            ):
                st.session_state["mood"] = m["id"]
                st.session_state["mood_history"].append(
                    {"date": selected_date, "mood": m["id"], "emoji": m["emoji"]}
                )
                st.session_state["page"] = "home"

def home():
    st.markdown("## 🏠 Overview")
    safe_img("dashboard_banner.png", width=260)

    current = get_mood_by_id(st.session_state["mood"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mood", current["emoji"])
    with c2:
        st.metric("Moods logged", len(st.session_state["mood_history"]))
    with c3:
        st.metric("Meals logged", len(st.session_state["food_log"]))
    with c4:
        last_bp = st.session_state["bp_log"][-1] if st.session_state["bp_log"] else None
        bp_text = f"{last_bp['sys']}/{last_bp['dia']} mmHg" if last_bp else "—"
        st.metric("Last BP", bp_text)

    st.markdown("### Quick access")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🍽️ Diet", use_container_width=True):
        st.session_state["page"] = "diet"
    if c2.button("📒 Food Diary", use_container_width=True):
        st.session_state["page"] = "food"
    if c3.button("💊 Medications", use_container_width=True):
        st.session_state["page"] = "meds"
    if c4.button("🩺 Doctors nearby", use_container_width=True):
        st.session_state["page"] = "doctors"

    st.markdown("### Recent activity")
    if st.session_state["food_log"]:
        last = st.session_state["food_log"][-1]
        st.write(f"Last meal: {last['desc'][:50]}…  |  {last['nutr']['Calories']} kcal")
    if st.session_state["bp_log"]:
        last_bp = st.session_state["bp_log"][-1]
        st.write(f"Last BP entry: {last_bp['sys']}/{last_bp['dia']} mmHg at {last_bp['time']}")

def diet_page():
    st.markdown("## 🥗 Diet & lifestyle")
    with st.form("diet_form"):
        veg_type = st.selectbox(
            "Diet type",
            ["Vegetarian", "Non‑vegetarian", "Vegan"],
            index=["Vegetarian", "Non‑vegetarian", "Vegan"].index(st.session_state["diet_type"]),
        )
        salt_limit = st.slider(
            "Salt restriction (g/day)",
            0.0, 6.0, float(st.session_state["salt_limit"]), 0.5
        )
        potassium_limit = st.selectbox(
            "Potassium restriction",
            ["None", "Mild", "Moderate", "Strict"],
            index=["None", "Mild", "Moderate", "Strict"].index(st.session_state["potassium_limit"])
        )
        fluids = st.slider(
            "Fluid allowance (L/day)",
            0.5, 3.0, float(st.session_state["fluid_allowance"]), 0.1
        )
        submitted = st.form_submit_button("Save profile")
    if submitted:
        st.session_state["diet_type"] = veg_type
        st.session_state["salt_limit"] = salt_limit
        st.session_state["potassium_limit"] = potassium_limit
        st.session_state["fluid_allowance"] = fluids
        st.success("Diet profile saved (demo only).")

    st.markdown("### Example renal‑friendly grocery")
    st.write("- Boiled / double‑boiled potatoes")
    st.write("- Rice, chapati, oats")
    st.write("- Pudhina chutney with less salt")
    st.info(
        "Kidney‑friendly eating often means limiting sodium, potassium and phosphorus, "
        "while getting enough energy and appropriate protein as advised by your team."
    )

def food_diary_page():
    st.markdown("## 🍽️ Food diary")
    with st.form("food_form", clear_on_submit=True):
        desc = st.text_area("Describe your meal")
        pic = st.file_uploader("Meal photo (optional)", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("Log meal")
    if submitted and desc.strip():
        nutr = nutri_estimator(desc)
        if pic:
            st.image(pic, width=220, caption="Nice choice!")
        st.json(nutr)

        feedback = ckd_diet_feedback(
            desc,
            potassium_limit=st.session_state["potassium_limit"],
            salt_limit_g=st.session_state["salt_limit"],
        )
        st.warning(feedback)

        st.session_state["food_log"].append(
            {
                "time": datetime.now().isoformat(timespec="minutes"),
                "desc": desc,
                "nutr": nutr,
            }
        )
        st.success("Meal logged.")

    st.markdown("### Recent meals")
    total_cal = 0
    total_protein = 0.0
    for rec in reversed(st.session_state["food_log"][-5:]):
        st.write(f"{rec['time']}: {rec['desc'][:40]}…  ({rec['nutr']['Calories']} kcal)")
        total_cal += rec["nutr"]["Calories"]
        total_protein += rec["nutr"]["Protein (g)"]

    if st.session_state["food_log"]:
        st.markdown("#### Today’s rough nutrition (demo)")
        st.write(f"Approx. calories from last {min(5, len(st.session_state['food_log']))} meals: {total_cal} kcal")
        st.write(f"Approx. protein: {round(total_protein, 1)} g")

def meds_page():
    st.markdown("## 💊 Medications")

    with st.form("add_med"):
        name = st.text_input("Medicine name")
        dose = st.text_input("Dose (e.g. 5 mg)")
        schedule = st.text_input("Schedule (e.g. Morning & Night)")
        add = st.form_submit_button("Add medicine")
    if add and name.strip():
        st.session_state["med_list"].append(
            {"name": name, "dose": dose, "schedule": schedule}
        )
        st.success("Medicine added.")

    if not st.session_state["med_list"]:
        st.info("No medicines added yet.")
        return

    st.markdown("### Today’s intake")
    today_str = str(date.today())
    for med in st.session_state["med_list"]:
        cols = st.columns([3, 2, 2])
        with cols[0]:
            st.write(f"**{med['name']}** – {med['dose']}")
            st.caption(med["schedule"])
        key_taken = f"taken_{med['name']}_{today_str}"
        with cols[1]:
            taken = st.checkbox("Taken", key=key_taken)
        with cols[2]:
            if taken:
                already_logged = any(
                    (rec["name"] == med["name"] and rec["time"].startswith(today_str))
                    for rec in st.session_state["med_intake"]
                )
                if not already_logged:
                    st.session_state["med_intake"].append(
                        {
                            "time": datetime.now().isoformat(timespec="minutes"),
                            "name": med["name"],
                            "taken": True,
                        }
                    )
                st.write("✅ logged")

    st.markdown("### Recent doses")
    for rec in reversed(st.session_state["med_intake"][-5:]):
        st.write(f"{rec['time']}: {rec['name']} taken")

def vitals_page():
    st.markdown("## 📊 Vitals & fluids")

    with st.form("vitals_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sys = st.number_input("Systolic BP (mmHg)", 80, 220, 120)
        with col2:
            dia = st.number_input("Diastolic BP (mmHg)", 40, 130, 80)
        with col3:
            hr = st.number_input("Heart rate (bpm)", 40, 180, 75)
        weight = st.number_input("Weight (kg)", 20.0, 200.0, 70.0, 0.1)
        urine = st.number_input("Urine output today (mL)", 0, 5000, 1500)
        submit = st.form_submit_button("Log values")

    if submit:
        now = datetime.now().isoformat(timespec="minutes")
        st.session_state["bp_log"].append(
            {"time": now, "sys": sys, "dia": dia, "hr": hr, "urine": urine}
        )
        st.session_state["weight_log"].append({"time": now, "weight": weight})
        st.success("Values logged.")

        # Very simple flags, not medical advice
        if sys >= 160 or dia >= 100:
            st.error("Blood pressure is quite high. Consider contacting your doctor.")
        if urine < 500:
            st.warning("Low urine output today. Discuss with your care team if this is unusual for you.")

    st.markdown("### Recent logs")
    if st.session_state["bp_log"]:
        last = st.session_state["bp_log"][-1]
        st.write(
            f"Last BP: {last['sys']}/{last['dia']} mmHg, HR {last['hr']} bpm, "
            f"Urine: {last['urine']} mL at {last['time']}"
        )
    if st.session_state["weight_log"]:
        last_w = st.session_state["weight_log"][-1]
        st.write(f"Last weight: {last_w['weight']} kg at {last_w['time']}")

def doctors_page():
    st.markdown("## 🩺 Search nearby nephrologists")
    city = st.text_input("Enter your city")
    if st.button("Search"):
        if not city.strip():
            st.warning("Please type a city.")
        else:
            st.markdown(f"**Results near {city.title()}** (demo data):")
            st.write("- Dr. Ravi Kumar – Nephrologist – 2 km")
            st.write("- Dr. Priya Mehta – Renal therapist – 3.5 km")

# ---------- Layout & routing ----------
st.set_page_config(page_title="DialySync CKD", page_icon="🩸", layout="wide")

st.title("🩸 DialySync CKD")
st.caption(
    "This tool supports self‑management for kidney health. "
    "It does not replace advice from your nephrologist or care team."
)

mood_calendar()
st.markdown("---")

if st.session_state["user_type"] is not None:
    page_choice = st.sidebar.radio(
        "Navigate",
        ["Home", "Log mood", "Diet", "Food diary", "Medications", "Vitals", "Doctors"],
        index=["home", "mood", "diet", "food", "meds", "vitals", "doctors"].index(
            st.session_state["page"]
        ) if st.session_state["page"] in ["home", "mood", "diet", "food", "meds", "vitals", "doctors"] else 0,
    )
    if page_choice == "Home":
        st.session_state["page"] = "home"
    elif page_choice == "Log mood":
        st.session_state["page"] = "mood"
    elif page_choice == "Diet":
        st.session_state["page"] = "diet"
    elif page_choice == "Food diary":
        st.session_state["page"] = "food"
    elif page_choice == "Medications":
        st.session_state["page"] = "meds"
    elif page_choice == "Vitals":
        st.session_state["page"] = "vitals"
    elif page_choice == "Doctors":
        st.session_state["page"] = "doctors"

if st.session_state["user_type"] is None or st.session_state["page"] == "welcome":
    welcome_screen()
elif st.session_state["page"] == "mood":
    mood_selector()
elif st.session_state["page"] == "diet":
    diet_page()
elif st.session_state["page"] == "food":
    food_diary_page()
elif st.session_state["page"] == "meds":
    meds_page()
elif st.session_state["page"] == "vitals":
    vitals_page()
elif st.session_state["page"] == "doctors":
    doctors_page()
else:
    home()
