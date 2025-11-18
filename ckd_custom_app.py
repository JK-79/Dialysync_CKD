import streamlit as st
from PIL import Image
from datetime import datetime, timedelta, date
import random, os, pickle
from pathlib import Path

# ------- IMAGE HANDLING ---------
IMG_PATH = lambda fn: os.path.join(os.path.dirname(__file__), fn)
def safe_img(fn, **kwargs):
    try: return st.image(IMG_PATH(fn), **kwargs)
    except Exception: return None

def image_to_b64(img_fn):
    import base64
    with open(IMG_PATH(img_fn), "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def section_bg(img_fn, opacity=0.68):
    if os.path.exists(IMG_PATH(img_fn)):
        st.markdown(
            f"""
            <style>
              .stApp {{
                background-image: url('data:image/png;base64,{image_to_b64(img_fn)}');
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                opacity: {opacity};
              }}
            </style>
            """,
            unsafe_allow_html=True
        )

# ------- MODEL LOADING --------
MODEL_PATH = Path(__file__).parent / "ckd_model.pkl"
if MODEL_PATH.exists():
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
else:
    model = None

# ------- APP CONFIG ---------
MOODS = [
    ("happy", "Feeling happy"),
    ("neutral", "Just okay"),
    ("tired", "Tired/exhausted"),
    ("sad", "Sad/down"),
    ("anxious", "Anxious/worried")
]

GROCERY = [
    ("Potatoes", "potato.png", "Soak/double-boil to reduce potassium"),
    ("Pudhina (mint)", "pudhina.png", "Flavorful, low potassium"),
    ("Carrots", "carrot.png", "Enjoy sparingly"),
    ("Oats", "oats.png", "Low sodium breakfast option"),
    ("Wheat flour", "wheat.png", "Healthy chapati base")
]

DOCTORS = {
    'delhi': [
        ("Dr. Ravi Kumar", "Nephrologist", "2km"),
        ("Dr. Priya Mehta", "Renal Therapist", "3.5km")
    ],
    'mumbai': [
        ("Dr. Aarav Shah", "Nephrologist", "5km"),
        ("Dr. Sneha Iyer", "Renal Dietitian", "6km")
    ],
    'default': [
        ("Dr. Aman Singh", "Nephrologist", "12km")
    ]
}

NUTRIT_DICT = {
    'rice': (150, 0.025, 1.1, 4, 3),
    'dal': (110, 0.26, 4, 11, 8),
    'roti': (90, 0.08, 3, 5, 2.5),
    'potato': (130, 0.42, 7, 7, 2),
    'carrots': (45, 0.32, 4, 3, 1),
    'oats': (150, 0.14, 2, 20, 5),
    'pudhina': (5, 0.01, 1, 9, 0.5),
    'wheat': (80, 0.10, 2, 4, 1.6)
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

def mood_chat_response(mood, msg):
    moodsugg = {
        'happy': "Wonderful! Keep a gratitude journal and fuel your health with mindful meals. 😊",
        'neutral': "Even neutral days need a little care. Try meditation or a pleasant walk.",
        'tired': "Tiredness is normal! Deep breaths or a small stretch often helps. Hydrate carefully.",
        'sad': "It's okay to feel down. Journaling or connecting with loved ones might help.",
        'anxious': "You are not alone. Practice the 4-4-4 breath. Would a calming food tip help?"
    }
    tip = moodsugg.get(mood, "Thank you for sharing your mood! Balanced nutrition and self-care always help.") + "\nTip: Small, regular meals and fluids as prescribed."
    return tip

# --------- State ---------
def state_init():
    for k,v in [('page','home'), ('user_type',None), ('mood',None), ('chat',[]), ('food_log',[]), ('appoint_date',None)]:
        if k not in st.session_state: st.session_state[k]=v
state_init()

# ----------- UI SECTIONS ----------
def home():
    section_bg('bg_dashboard.png', opacity=0.65)
    st.markdown("# CKD Care App")
    st.markdown("#### For patients & caregivers on the CKD journey")
    col1, col2 = st.columns(2)
    with col1:
        safe_img('patient.png', width=90, caption="Patient")
        if st.button("I am a Patient", use_container_width=True):
            st.session_state['user_type']='Patient'
            st.session_state['page']='mood_selector'
    with col2:
        safe_img('caregiver.png', width=90, caption="Caregiver")
        if st.button("I am a Caregiver", use_container_width=True):
            st.session_state['user_type']='Caregiver'
            st.session_state['page']='mood_selector'

def mood_selector():
    section_bg('bg_dashboard.png', opacity=0.66)
    st.markdown(f"## {st.session_state['user_type']} — how are you today?")
    st.write("_Select the face matching your mood!_ (Try clicking)")
    cols = st.columns(len(MOODS))
    for i, (mood, desc) in enumerate(MOODS):
        with cols[i]:
            safe_img(f"mood_{mood}.png", width=48, caption="")
            if st.button(desc, key=f"mood_{mood}"):
                st.session_state['mood']=mood
                st.session_state['page']='dashboard'

def main_menu():
    section_bg('bg_dashboard.png', opacity=0.69)
    st.sidebar.title(f"Welcome, {st.session_state['user_type']}")
    nav = st.sidebar.radio('Navigate:', [
        "Dashboard",
        "Diet & Lifestyle",
        "Food Diary",
        "Medications",
        "Consultations",
        "Community Support",
        "Records & Reports",
        "Doctor Finder",
        "Log out"
    ], key='navsel')
    if nav=="Dashboard": dashboard()
    elif nav=="Diet & Lifestyle": diet()
    elif nav=="Food Diary": food_diary()
    elif nav=="Medications": medication()
    elif nav=="Consultations": consultations()
    elif nav=="Community Support": community()
    elif nav=="Records & Reports": records_reports()
    elif nav=="Doctor Finder": doctor_finder()
    elif nav=="Log out":
        st.session_state['page']='home'
        st.session_state['user_type']=None
        st.experimental_rerun()

def dashboard():
    section_bg('bg_dashboard.png', opacity=0.62)
    st.markdown(f"# CKD Dashboard for {st.session_state['user_type']}")
    mood = st.session_state['mood']
    safe_img(f"mood_{mood}.png", width=70)
    st.markdown(f"**Today's Mood:** {dict(MOODS)[mood]}")
    st.write("---")
    st.write("## Your Quick Stats:")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("BP", "124/82 mmHg", "+2")
    with c2: st.metric("Weight", "67.5 kg", "-0.5")
    with c3: st.metric("Glucose", "104 mg/dL", "Stable")
    # ML CKD prediction widget
    if model:
        st.markdown("> **Demo ML: Predict your CKD risk:**")
        bp = st.slider("BP (mmHg)", 90, 180, 124)
        glucose = st.slider("Glucose (mg/dL)", 60, 220, 104)
        age = st.slider("Age", 18, 90, 45)
        protein = st.slider("Daily protein intake (g)", 10, 100, 45)
        if st.button("Estimate CKD Progression Risk"):
            X = [[bp, glucose, age, protein]]
            prob = model.predict_proba(X)[0,1]
            if prob > 0.7:
                st.error(f"High risk of CKD progression! (Risk: {prob:.2f})")
            else:
                st.success(f"CKD risk controlled. Continue healthy routines. (Risk: {prob:.2f})")
    st.write("\n---")
    if st.button("Go to Mood Coach/Chatbot"):
        st.session_state['page']='chatbot'

def diet():
    section_bg('bg_diet.png', opacity=0.67)
    st.markdown("# Renal Diet & Lifestyle")
    st.write("Healthy food choices lower kidney workload — let's plan together.")
    st.markdown("### Grocery List:")
    gcols = st.columns(len(GROCERY))
    for i, (food, ico, det) in enumerate(GROCERY):
        with gcols[i]:
            safe_img(ico, width=38)
            st.markdown(f"**{food}**\n_{det}_")
    st.info("Tip: Double-boil potatoes and enjoy pudhina for flavor without the salt!")
    st.markdown("### High potassium foods (limit): " + ", ".join(HIGH_POTASSIUM))
    st.markdown("### Low potassium foods (enjoy safely): " + ", ".join(LOW_POTASSIUM))

def food_diary():
    section_bg('bg_food.png', opacity=0.68)
    st.markdown("# Meal Log & Nutrition Estimate 🥗")
    with st.form("foodlogger", clear_on_submit=True):
        meal = st.text_area("Meal description", help="e.g. Dal, rice, carrots")
        pic = st.file_uploader("Photo of your meal (optional)", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("Add Meal to Diary")
    if submitted and meal:
        report = nutri_estimator(meal)
        if pic:
            st.image(pic, width=200)
            st.success("Wow, you are taking care of yourself!")
        else:
            st.info("Photographing your meal is a great step!")
        st.write("## Estimated Nutrition:")
        st.write(report)
        st.session_state['food_log'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'desc': meal,
            'img': pic.name if pic else None,
            'nutr': report
        })
        st.success("Meal registered in your food log!")
    st.write("---")
    st.markdown("### Recent Meals:")
    if len(st.session_state['food_log'])==0:
        st.info("No meals yet!")
    for rec in reversed(st.session_state['food_log'][-5:]):
        st.markdown(f"**[{rec['time']}]** _{rec['desc']}_")
        st.write(rec['nutr'])
        if rec['img']:
            safe_img(rec['img'], width=100)

def medication():
    section_bg('bg_meds.png', opacity=0.66)
    st.markdown("# Medication Tracker 🕒💊")
    with st.form("medform", clear_on_submit=True):
        med = st.text_input("Medication name")
        dose = st.text_input("Dose & Timing", help="e.g., 1 tab morning/evening")
        added = st.form_submit_button("Add Medication")
    if added and med and dose:
        st.success(f"Registered: {med} — {dose}")
    st.info("For best results, follow your plan and set alarms on your phone!")

def consultations():
    section_bg('bg_doc.png', opacity=0.65)
    st.markdown("# Book a Consultation 📅")
    st.write("Choose a specialist or book Creatinine test.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Choose specialist:")
        st.selectbox("Doctor/Therapist", [
            "Dr. Ravi Kumar, Nephrologist",
            "Ms. Priya Singh, Dietitian",
            "Dr. Sneha Iyer, Psychologist",
            "Dr. Aman Singh, Physiotherapist"
        ])
        st.button("Book Appointment")
    with col2:
        st.markdown("#### Creatinine Test Appointment:")
        d = st.date_input("Choose appointment date", value=date.today()+timedelta(days=2))
        st.session_state['appoint_date'] = d
        st.write(f"Appointment booked for Creatinine test on {d.strftime('%b %d, %Y')}")

def community():
    section_bg('bg_community.png', opacity=0.62)
    st.markdown("# CKD Community Support 💬")
    st.write("Share experiences, tips, or support:")
    post = st.text_area("Type your message:")
    if st.button("Post") and post.strip():
        st.success(f"Message posted!")
    st.info("Recent posts:")
    st.write("- *How to manage long dialysis days?* — Renu")
    st.write("- *My low-salt snack ideas!* — Rajat")

def records_reports():
    section_bg('bg_meds.png', opacity=0.57)
    st.markdown("# Records & Reports 📑")
    doc = st.file_uploader("Upload reports/photos (PDF,JPG,PNG)", type=["pdf","jpg","jpeg","png"])
    if doc:
        st.success(f"Uploaded: {doc.name}")
    st.markdown("---")
    st.markdown("### Creatinine Test Appointment:")
    d = st.date_input("Pick a date:", value=date.today()+timedelta(days=3))
    st.write(f"Appointment: Creatinine test on {d.strftime('%A, %b %d, %Y')}")

def doctor_finder():
    section_bg('bg_doc.png', opacity=0.61)
    st.markdown("# Search Nearby Doctors 🏥")
    loc = st.text_input("Your city (e.g., Delhi, Mumbai)", key="docloc")
    if st.button("Search") and loc.strip():
        docs = DOCTORS.get(loc.lower(), DOCTORS['default'])
        st.success(f"{len(docs)} doctor(s) found in or near {loc.title()}")
        for name, specialty, dist in docs:
            st.markdown(f"- **{name}**, *{specialty}* ({dist})")

def chatbot():
    section_bg('bg_dashboard.png', opacity=0.59)
    mood = st.session_state.get('mood', 'neutral')
    safe_img(f"mood_{mood}.png", width=45)
    st.markdown(f"# Mood Coach & Chatbot")
    st.write("Chat about your feelings and get calm, supportive tips!")
    with st.form("moodchat", clear_on_submit=True):
        msg = st.text_input("How are you feeling today? (Describe in your words)")
        submit = st.form_submit_button("Send")
    if submit and msg:
        reply = mood_chat_response(mood, msg)
        st.session_state['chat'].append((msg, reply))
    for (user_txt, resp) in reversed(st.session_state['chat'][-5:]):
        st.markdown(f"**You:** {user_txt}")
        st.markdown(f"> MoodBot: {resp}")
    if st.button("Back to Dashboard"):
        st.session_state['page']='dashboard'

# -------- Main App Router ---------
if st.session_state['page'] == 'home':
    home()
elif st.session_state['page'] == 'mood_selector':
    mood_selector()
elif st.session_state['page'] == 'dashboard':
    main_menu()
elif st.session_state['page'] == 'chatbot':
    chatbot()
