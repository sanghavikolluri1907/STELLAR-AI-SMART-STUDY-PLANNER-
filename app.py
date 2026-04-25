"""
app.py — AI Smart Study Planner
Entry point. Run with: streamlit run app.py

Features:
  • User authentication (register / login)
  • Personalized dashboard with streaks, XP, badges
  • Study planner (add / view / edit / complete tasks)
  • AI study suggestions & schedule generator
  • Pomodoro timer with sound alerts
  • Progress analytics (Plotly charts)
  • Gamification system (XP, levels, badges)
  • Voice assistant (speech_recognition + pyttsx3)
  • Daily goal tracker
  • Focus mode
  • Motivational quotes & tips
"""

import streamlit as st
import time
from datetime import date, timedelta

# ── Internal modules ──────────────────────────────────────────────────────────
from database import (
    init_db, get_tasks, get_study_sessions,
    log_study_session, upsert_daily_goal, get_daily_goal, get_user,
)
from auth       import register_user, login_user, logout_user, require_login
from planner    import render_planner
from ai_features import (
    get_random_quote, get_tip_of_day,
    generate_study_suggestions, generate_daily_schedule, identify_weak_subjects,
)
from rewards    import get_badge, get_level_title, xp_to_next_level
from visualization import (
    weekly_study_hours_chart, subject_distribution_chart,
    task_completion_trend, priority_breakdown_chart, xp_gauge,
)
from voice_assistant import voice_assistant_ui

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="STELLAR",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base dark theme ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F172A;
    color: #E2E8F0;
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E1B4B 0%, #0F172A 100%);
    border-right: 1px solid rgba(124,58,237,0.3);
}
/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid rgba(124,58,237,0.4);
    border-radius: 14px;
    padding: 16px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #3B82F6);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(124,58,237,0.5);
}
/* ── Forms ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > textarea {
    background: #1E293B !important;
    border: 1px solid rgba(124,58,237,0.4) !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
}
/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1E293B;
    border-radius: 12px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #94A3B8;
    border-radius: 8px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#7C3AED,#3B82F6) !important;
    color: white !important;
}
/* ── Progress bars ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #06B6D4) !important;
    border-radius: 99px !important;
}
/* ── Expander ── */
.streamlit-expanderHeader {
    background: #1E293B !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
}
/* ── Info / success / warning ── */
.stAlert { border-radius: 12px !important; }
/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    background: #1E293B;
    border-radius: 12px;
}
/* ── Custom card component ── */
.sp-card {
    background: linear-gradient(135deg,#1E293B,#0F172A);
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.35);
}
.sp-card h3 { margin-top: 0; color: #C4B5FD; }
.sp-badge {
    display: inline-block;
    background: linear-gradient(135deg,#7C3AED,#3B82F6);
    color: white;
    border-radius: 99px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    margin: 4px 2px;
}
.sp-schedule-row {
    background: #1E293B;
    border-left: 4px solid #7C3AED;
    border-radius: 0 10px 10px 0;
    padding: 10px 16px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sp-schedule-break {
    border-left-color: #06B6D4 !important;
}
.focus-overlay {
    position: fixed; inset: 0; z-index: 9999;
    background: #070B14;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
}
/* ── Sidebar nav ── */
.nav-section { color: #7C3AED; font-weight: 700; font-size: 11px;
    letter-spacing: 1.5px; text-transform: uppercase; margin: 18px 0 6px; }
/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #7C3AED; border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────────────────────
init_db()

# Session-state defaults
for key, default in [
    ("logged_in", False), ("user_id", None), ("username", ""),
    ("xp", 0), ("level", 1), ("streak", 0),
    ("focus_mode", False), ("page", "Dashboard"),
    ("pomo_running", False), ("pomo_start", None),
    ("pomo_end", None), ("pomo_duration", None),
    ("pomo_mode", "study"), ("pomo_sessions", 0),
    ("water_reminder_active", False),
    ("water_reminder_interval", 30),
    ("water_last_drink", None),
    ("water_last_reminder", None),
    ("water_glasses_today", 0),
    ("water_alert_sent", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────────────────────────────────────
# FOCUS MODE + TRACKER (FIXED)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as components

def focus_tracker_component():
    components.html(
"""
<div id="status" style="color:white;text-align:center;font-weight:bold;">
    Focus Tracker: Initializing...
</div>
<div id="error-container" style="color:#ff4b4b;text-align:center;margin-top:10px;font-size:12px;"></div>

<video id="video" width="200" height="150" autoplay muted style="display:none;"></video>
<audio id="alertSound" src="https://www.soundjay.com/button/beep-07.wav"></audio>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.15.0/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/blazeface@0.0.7"></script>

<script>
const statusDiv = document.getElementById('status');
const errorDiv = document.getElementById('error-container');
const video = document.getElementById('video');
const alertSound = document.getElementById('alertSound');

let distractedTime = 0;
let model = null;

// Check if required libraries are loaded
function checkLibraries() {
    return new Promise((resolve) => {
        let attempts = 0;
        const checkInterval = setInterval(() => {
            attempts++;
            if (typeof tf !== 'undefined' && typeof blazeface !== 'undefined') {
                clearInterval(checkInterval);
                resolve(true);
            } else if (attempts > 30) { // 30 * 500ms = 15 seconds timeout
                clearInterval(checkInterval);
                resolve(false);
            }
        }, 500);
    });
}

async function setupCamera() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera not supported on this device');
        }
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480, facingMode: 'user' } 
        });
        video.srcObject = stream;
        return new Promise((resolve, reject) => {
            video.onloadedmetadata = () => resolve(video);
            setTimeout(() => reject(new Error('Camera initialization timeout')), 5000);
        });
    } catch (err) {
        statusDiv.innerText = "❌ Camera Access Denied!";
        errorDiv.innerText = err.message;
        throw err;
    }
}

async function main() {
    try {
        // Check if libraries loaded
        statusDiv.innerText = "📥 Loading Libraries...";
        const libsLoaded = await checkLibraries();
        if (!libsLoaded) {
            throw new Error('AI libraries failed to load from CDN. Check your internet connection.');
        }

        statusDiv.innerText = "📷 Requesting Camera...";
        await setupCamera();

        statusDiv.innerText = "🤖 Loading AI Model...";
        
        model = await blazeface.load();
        
        statusDiv.innerText = "✅ Focus Tracker Active";
        errorDiv.innerText = "";

        // Detection loop
        const detectionLoop = async () => {
            try {
                if (!model) return;
                
                const predictions = await model.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    statusDiv.innerText = "🎯 Focused";
                    statusDiv.style.color = "#00ffcc";
                    distractedTime = 0;
                } else {
                    statusDiv.innerText = "❌ No Face Detected";
                    statusDiv.style.color = "#ffbd45";
                    distractedTime++;
                    
                    if (distractedTime >= 3) {
                        try {
                            alertSound.play();
                        } catch (e) {
                            console.log('Could not play alert');
                        }
                        distractedTime = 0;
                    }
                }
            } catch (err) {
                console.error('Detection error:', err);
            }
            
            requestAnimationFrame(detectionLoop);
        };
        
        detectionLoop();

    } catch (err) {
        statusDiv.innerText = "❌ Error Loading Model";
        statusDiv.style.color = "#ff4b4b";
        errorDiv.innerText = "Error: " + err.message + ". Try refreshing the page or check your internet.";
        console.error('Focus Mode Error:', err);
    }
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', main);
} else {
    main();
}
</script>
""",
height=150
)

# ─────────────────────────────────────────────────────────────────────────────
# FOCUS MODE OVERLAY (UPDATED)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.focus_mode:
    st.markdown("""
    <div style='text-align:center;padding:40px 0'>
        <h1 style='font-size:60px;margin-bottom:0'>🎯</h1>
        <h1 style='color:#C4B5FD;font-size:36px'>Focus Mode Activated</h1>
        <p style='color:#94A3B8;font-size:18px'>
            AI is monitoring your focus via webcam 👁️
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ✅ Webcam AI tracking
    focus_tracker_component()

    if st.button("❌ Exit Focus Mode", use_container_width=True):
        st.session_state.focus_mode = False
        st.rerun()

    st.stop()
# --- HOW TO CALL IT IN YOUR STREAMLIT APP ---
if st.sidebar.button("🎯 Focus Mode"):
    st.title("Focus Mode Activated")
    focus_tracker_component() # This starts the webcam tracking
    st.write("The AI is now monitoring your focus levels via webcam.")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH PAGES
# ─────────────────────────────────────────────────────────────────────────────
def render_auth():
    st.markdown("""
    <div style='text-align:center;padding:40px 0 20px'>
        <span style='font-size:64px'>🎓</span>
        <h1 style='color:#C4B5FD;margin:8px 0 4px;font-size:36px'>STELLAR</h1>
        <p style='color:#94A3B8;font-size:16px'>Your intelligent academic companion</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_reg = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username", placeholder="your_username")
                pwd   = st.text_input("Password", type="password", placeholder="••••••••")
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            if login_btn:
                ok, msg = login_user(uname, pwd)
                if ok:
                    st.success(msg)
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("---")
            st.markdown("**Demo credentials:** `demo` / `demo123`")
            if st.button("⚡ Quick Demo Login", use_container_width=True):
                # Ensure demo user exists
                from database import create_user
                from auth import hash_password
                create_user("demo", hash_password("demo123"), "demo@study.ai")
                ok, msg = login_user("demo", "demo123")
                if ok:
                    _seed_demo_data(st.session_state.user_id)
                    st.rerun()

        with tab_reg:
            with st.form("reg_form"):
                r_uname = st.text_input("Username", placeholder="choose a username", key="r_u")
                r_email = st.text_input("Email (optional)", placeholder="you@email.com", key="r_e")
                r_pwd   = st.text_input("Password", type="password", key="r_p")
                r_pwd2  = st.text_input("Confirm Password", type="password", key="r_p2")
                reg_btn = st.form_submit_button("✨ Create Account", use_container_width=True)
            if reg_btn:
                if r_pwd != r_pwd2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(r_uname, r_pwd, r_email)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def _seed_demo_data(user_id: int):
    """Insert sample tasks for the demo account if none exist."""
    from database import get_tasks, add_task, log_study_session
    if get_tasks(user_id):
        return
    today = date.today()
    samples = [
        ("Mathematics",      "Calculus Integration Practice",   today + timedelta(days=1), "High",   2.0),
        ("Physics",          "Electrostatics Chapter Review",   today + timedelta(days=2), "High",   1.5),
        ("Chemistry",        "Organic Reactions Memorisation",  today + timedelta(days=3), "Medium", 1.0),
        ("English",          "Essay Writing Draft",             today + timedelta(days=5), "Medium", 2.0),
        ("Computer Science", "Data Structures — Trees",         today + timedelta(days=2), "High",   1.5),
        ("Mathematics",      "Probability Problem Set",         today + timedelta(days=4), "Low",    1.0),
        ("Biology",          "Cell Division Notes",             today + timedelta(days=7), "Low",    1.0),
    ]
    for subj, name, dl, pri, hrs in samples:
        add_task(user_id, subj, name, str(dl), pri, hrs)
    # Seed some study sessions
    for i in range(7):
        d = str(today - timedelta(days=i))
        for subj, mins in [("Mathematics", 60), ("Physics", 45), ("Chemistry", 30)]:
            log_study_session(user_id, subj, mins)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:16px 0 8px'>
            <span style='font-size:42px'>🎓</span>
            <h2 style='color:#C4B5FD;margin:4px 0;font-size:20px'>Study<span style='color:#06B6D4'>AI</span></h2>
        </div>
        """, unsafe_allow_html=True)

        # User info pill
        badge_name, _ = get_badge(st.session_state.xp)
        st.markdown(f"""
        <div class='sp-card' style='text-align:center;padding:14px'>
            <p style='margin:0;font-size:22px'>👤 {st.session_state.username}</p>
            <span class='sp-badge'>{badge_name}</span><br>
            <small style='color:#94A3B8'>Level {st.session_state.level} · {st.session_state.xp} XP · 🔥 {st.session_state.streak} day streak</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='nav-section'>Navigation</div>", unsafe_allow_html=True)
        pages = {
            "🏠 Dashboard":          "Dashboard",
            "📚 Study Planner":      "Planner",
            "🤖 AI Features":        "AI Features",
            "⏱️ Productivity Tools": "Productivity",
            "📊 Analytics":          "Analytics",
            "🎙️ Voice Assistant":    "Voice",
            "🏆 Achievements":       "Achievements",
        }
        for label, key in pages.items():
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.page = key

        st.markdown("<div class='nav-section'>Quick Actions</div>", unsafe_allow_html=True)
        if st.button("🎯 Focus Mode", use_container_width=True):
            st.session_state.focus_mode = True
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    uid = st.session_state.user_id

    # Header
    st.markdown(f"""
    <div class='sp-card'>
        <h2 style='margin:0;font-size:28px'>👋 Welcome back, <span style='color:#A78BFA'>{st.session_state.username}</span>!</h2>
        <p style='color:#94A3B8;margin:6px 0 0'>Today is {date.today().strftime('%A, %B %d %Y')} · Keep the momentum going! 🚀</p>
    </div>
    """, unsafe_allow_html=True)

    tasks = get_tasks(uid)
    total      = len(tasks)
    completed  = sum(1 for t in tasks if t["status"] == "Completed")
    pending    = total - completed
    today_str  = str(date.today())
    due_today  = [t for t in tasks if t["deadline"] == today_str and t["status"] == "Pending"]

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total Tasks",     total)
    c2.metric("✅ Completed",        completed)
    c3.metric("⏳ Pending",          pending)
    c4.metric("⚡ XP",              st.session_state.xp)

    # Completion bar
    if total:
        pct = completed / total
        st.markdown(f"**Task Completion: {pct*100:.0f}%**")
        st.progress(pct)

    # XP level bar
    xp_cur, xp_needed = xp_to_next_level(st.session_state.xp)
    st.markdown(f"**Level {st.session_state.level} XP: {xp_cur}/{xp_needed}**")
    st.progress(xp_cur / xp_needed)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Due today
        st.markdown("### 📅 Due Today")
        if due_today:
            for t in due_today:
                emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[t["priority"]]
                st.markdown(f"""
                <div class='sp-card' style='padding:12px 16px'>
                    {emoji} <strong>{t['subject']}</strong> — {t['task_name']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("🎉 Nothing due today! Great planning!")

        # Tip of the day
        st.markdown("### 💡 Tip of the Day")
        st.info(get_tip_of_day())

    with col_right:
        # Streak card
        streak = st.session_state.streak
        streak_color = "#F59E0B" if streak >= 3 else "#94A3B8"
        st.markdown(f"""
        <div class='sp-card' style='text-align:center'>
            <h3 style='color:#F59E0B;font-size:40px;margin:0'>🔥 {streak}</h3>
            <p style='color:#94A3B8;margin:4px 0'>Day Streak</p>
            <small style='color:#64748B'>Log in daily to maintain your streak!</small>
        </div>
        """, unsafe_allow_html=True)

        # Badge
        badge_name, badge_desc = get_badge(st.session_state.xp)
        level_title = get_level_title(st.session_state.level)
        st.markdown(f"""
        <div class='sp-card' style='text-align:center'>
            <h3 style='margin:0;font-size:28px'>{badge_name}</h3>
            <p style='color:#94A3B8;margin:4px 0;font-size:13px'>{badge_desc}</p>
            <span class='sp-badge'>{level_title}</span>
        </div>
        """, unsafe_allow_html=True)

        # Motivational quote
        st.markdown("### 💬 Quote")
        st.markdown(f"""
        <div class='sp-card'>
            <p style='font-style:italic;color:#C4B5FD;margin:0'>{get_random_quote()}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 New Quote", use_container_width=True):
            st.rerun()

    # Weekly chart
    st.markdown("### 📈 This Week at a Glance")
    sessions = get_study_sessions(uid, days=7)
    st.plotly_chart(weekly_study_hours_chart(sessions), use_container_width=True)


def page_ai_features():
    uid = st.session_state.user_id
    tasks = get_tasks(uid)

    st.markdown("## 🤖 AI Features")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Study Suggestions", "📅 Daily Schedule",
        "⚠️ Weak Subjects", "💡 Motivation",
    ])

    with tab1:
        st.markdown("### 🧠 AI Study Order Recommendation")
        st.markdown("_Based on your deadlines and priority levels:_")
        suggestions = generate_study_suggestions(tasks)
        for s in suggestions:
            st.markdown(f"""
            <div class='sp-card' style='padding:12px 16px'>
                {s}
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### 📅 AI Daily Schedule Generator")
        start_hour = st.slider("Start studying at (hour)", 6, 12, 8)
        if st.button("🤖 Generate My Schedule", use_container_width=True):
            schedule = generate_daily_schedule(tasks, start_hour)
            if not schedule:
                st.info("No pending tasks to schedule. Add tasks first!")
            else:
                st.markdown("#### 🗓️ Today's AI-Generated Pomodoro Schedule")
                for slot in schedule:
                    is_break = "Break" in slot["task"]
                    border   = "#06B6D4" if is_break else "#7C3AED"
                    st.markdown(f"""
                    <div style='background:#1E293B;border-left:4px solid {border};
                         border-radius:0 10px 10px 0;padding:10px 16px;
                         margin-bottom:6px;display:flex;justify-content:space-between'>
                        <div>
                            <strong style='color:#C4B5FD'>{slot["time"]}</strong>
                            &nbsp;·&nbsp;{slot["type"]}
                        </div>
                        <div style='color:#94A3B8'>{slot["subject"]} — {slot["task"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### ⚠️ Weak Subject Detector")
        weak = identify_weak_subjects(tasks)
        for w in weak:
            st.markdown(f"""
            <div class='sp-card' style='border-color:rgba(239,68,68,0.5);padding:12px 16px'>
                {w}
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("### 💬 Motivation Station")
        st.markdown(f"""
        <div class='sp-card' style='text-align:center;padding:30px'>
            <p style='font-size:20px;font-style:italic;color:#C4B5FD'>{get_random_quote()}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Motivate Me!", use_container_width=True):
            st.rerun()
        st.markdown("---")
        st.markdown(f"### 💡 Today's Study Tip\n{get_tip_of_day()}")


def page_productivity():
    uid = st.session_state.user_id

    st.markdown("## ⏱️ Productivity Tools")
    tab_pomo, tab_goal, tab_water = st.tabs(["🍅 Pomodoro Timer", "🎯 Daily Goal Tracker", "💧 Hydration Reminder"])

    # ── POMODORO ──────────────────────────────────────────────────────────
    with tab_pomo:
        st.markdown("### 🍅 Pomodoro Timer")

        DURATIONS = {"study": 25 * 60, "short_break": 5 * 60, "long_break": 15 * 60}
        mode_labels = {"study": "🎯 Study (25 min)", "short_break": "☕ Short Break (5 min)", "long_break": "🛋️ Long Break (15 min)"}

        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            mode = st.radio("Mode", list(DURATIONS.keys()),
                            format_func=lambda m: mode_labels[m], horizontal=True,
                            key="pomo_mode_select")

            duration = DURATIONS[mode]
            pomo_placeholder = st.empty()

            c1, c2, c3 = st.columns(3)
            start_btn = c1.button("▶ Start",  use_container_width=True)
            stop_btn  = c2.button("⏹ Stop",   use_container_width=True, key="pomo_stop")
            reset_btn = c3.button("↺ Reset",  use_container_width=True, key="pomo_reset")

            sessions_done = st.session_state.pomo_sessions
            st.markdown(f"**Sessions completed today: 🍅 × {sessions_done}**")

            subject_log = st.selectbox("Log session to subject:", [
                "Mathematics","Physics","Chemistry","Biology",
                "English","Computer Science","Other",
            ], key="pomo_subject")

            if start_btn:
                st.session_state.pomo_running = True
                st.session_state.pomo_start   = time.time()
                st.session_state.pomo_end     = st.session_state.pomo_start + duration
                st.session_state.pomo_duration = duration
                st.session_state.pomo_mode    = mode
                st.success("🚀 Pomodoro started! Stay focused.")
                show_notification("Pomodoro started", f"{mode_labels[mode]} has begun.")

            if stop_btn or reset_btn:
                if st.session_state.pomo_running and stop_btn:
                    elapsed = int(time.time() - (st.session_state.pomo_start or time.time()))
                    if elapsed >= 60:
                        log_study_session(uid, subject_log, elapsed // 60)
                        st.success(f"✅ Logged {elapsed//60} min of {subject_log}")
                        if mode == "study":
                            st.session_state.pomo_sessions += 1
                    st.warning("⏸️ Pomodoro paused.")
                    show_notification("Pomodoro paused", "Your session has been paused.")
                elif reset_btn:
                    st.info("↺ Pomodoro timer reset.")
                st.session_state.pomo_running = False
                st.session_state.pomo_start   = None
                st.session_state.pomo_end     = None
                st.session_state.pomo_duration = None

            if st.session_state.pomo_running and st.session_state.pomo_end:
                remaining = max(int(st.session_state.pomo_end - time.time()), 0)
                mins, secs = divmod(remaining, 60)
                current_mode = st.session_state.pomo_mode
                current_duration = st.session_state.pomo_duration or duration

                color = "#7C3AED" if current_mode == "study" else "#06B6D4"
                pomo_placeholder.markdown(f"""
                <div style='text-align:center;padding:20px 0'>
                    <div style='font-size:72px;font-weight:800;color:{color};
                         font-family:monospace;letter-spacing:4px'>
                        {mins:02d}:{secs:02d}
                    </div>
                    <p style='color:#94A3B8;margin:4px 0'>{mode_labels[current_mode]}</p>
                    <p style='color:#64748B;font-size:13px'>Stay focused! You can do this 💪</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress((current_duration - remaining) / current_duration)

                if remaining == 0:
                    st.balloons()
                    st.success("🎉 Session complete! Take a well-deserved break.")
                    st.warning("⏰ Time's up! Switch mode or take a break.")
                    show_notification("Pomodoro complete!", "Great work — your session is finished.")
                    play_alert_sound()
                    st.session_state.pomo_running = False
                    st.session_state.pomo_start = None
                    st.session_state.pomo_end = None
                    st.session_state.pomo_duration = None
                    if current_mode == "study":
                        st.session_state.pomo_sessions += 1
                        log_study_session(uid, subject_log, 25)
                else:
                    time.sleep(1)
                    st.rerun()
            else:
                pomo_placeholder.markdown(f"""
                <div style='text-align:center;padding:20px 0'>
                    <div style='font-size:72px;font-weight:800;color:#4B5563;font-family:monospace'>
                        {DURATIONS[mode]//60:02d}:00
                    </div>
                    <p style='color:#64748B'>Press Start to begin</p>
                </div>
                """, unsafe_allow_html=True)

    # ── DAILY GOAL TRACKER ────────────────────────────────────────────────
    with tab_goal:
        st.markdown("### 🎯 Daily Goal Tracker")
        existing = get_daily_goal(uid)

        with st.form("goal_form"):
            col1, col2 = st.columns(2)
            default_h = float(existing["target_hours"]) if existing else 4.0
            default_t = int(existing["target_tasks"]) if existing else 3
            with col1:
                target_h = st.slider("Target Study Hours", 1.0, 12.0, default_h, 0.5)
            with col2:
                target_t = st.number_input("Target Tasks", 1, 20, default_t)
            save_goal = st.form_submit_button("💾 Save Daily Goals", use_container_width=True)

        if save_goal:
            upsert_daily_goal(uid, target_h, target_t)
            st.success("✅ Daily goals saved!")
            st.rerun()

        goal = get_daily_goal(uid)
        if goal:
            tasks = get_tasks(uid)
            done_today = sum(
                1 for t in tasks
                if t["status"] == "Completed" and
                (t.get("completed_at") or "")[:10] == str(date.today())
            )
            sessions = get_study_sessions(uid, days=1)
            hours_today = sum(s["total_min"] for s in sessions) / 60 if sessions else 0

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📚 Study Hours Progress**")
                h_pct = min(hours_today / goal["target_hours"], 1.0)
                st.progress(h_pct)
                st.caption(f"{hours_today:.1f}h / {goal['target_hours']}h")
            with col2:
                st.markdown("**✅ Tasks Progress**")
                t_pct = min(done_today / goal["target_tasks"], 1.0) if goal["target_tasks"] else 0
                st.progress(t_pct)
                st.caption(f"{done_today} / {goal['target_tasks']} tasks")

    # ── HYDRATION REMINDER ─────────────────────────────────────────
    with tab_water:
        st.markdown("### 💧 Hydration Reminder")
        st.markdown("Stay healthy while you study by drinking water regularly.")

        interval = st.slider(
            "Remind me every (minutes)",
            15, 120,
            st.session_state.water_reminder_interval,
            5,
            help="Choose how often you want to receive a hydration reminder."
        )
        st.session_state.water_reminder_interval = interval

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.session_state.water_reminder_active:
                if st.button("⏹ Stop reminders", use_container_width=True):
                    st.session_state.water_reminder_active = False
                    st.success("Hydration reminders stopped.")
            else:
                if st.button("▶ Start reminders", use_container_width=True):
                    now = time.time()
                    st.session_state.water_reminder_active = True
                    st.session_state.water_last_reminder = st.session_state.water_last_reminder or now
                    st.session_state.water_last_drink = st.session_state.water_last_drink or now
                    st.session_state.water_alert_sent = False
                    st.success("Hydration reminders started.")
        with col2:
            if st.button("💧 I drank water", use_container_width=True):
                now = time.time()
                st.session_state.water_last_drink = now
                st.session_state.water_last_reminder = now
                st.session_state.water_glasses_today += 1
                st.session_state.water_alert_sent = False
                st.success("Water intake logged.")

        last_drink = "Never"
        next_due_text = "—"
        reminder_message = "Reminders are paused."

        if st.session_state.water_last_drink:
            last_drink = date.fromtimestamp(st.session_state.water_last_drink).strftime("%H:%M")

        if st.session_state.water_reminder_active:
            now = time.time()
            last_reminder = st.session_state.water_last_reminder or now
            next_due = last_reminder + interval * 60
            remaining = max(int(next_due - now), 0)
            mins, secs = divmod(remaining, 60)
            next_due_text = f"{mins:02d}:{secs:02d}"

            if remaining == 0 and not st.session_state.water_alert_sent:
                show_notification("💧 Time to drink water", f"Drink a glass of water every {interval} minutes.")
                play_alert_sound()
                st.session_state.water_alert_sent = True
                reminder_message = "⏰ Time to hydrate now!"
            elif remaining > 0:
                reminder_message = f"Next reminder in {mins:02d}:{secs:02d}."
            else:
                reminder_message = "⏰ Time to hydrate now!"

        col1, col2, col3 = st.columns(3)
        col1.metric("Last water logged", last_drink)
        col2.metric("Next reminder", next_due_text)
        col3.metric("Glasses today", st.session_state.water_glasses_today)

        st.info(reminder_message)
        if st.session_state.water_reminder_active:
            st.rerun()


def page_analytics():
    uid = st.session_state.user_id
    tasks = get_tasks(uid)
    sessions = get_study_sessions(uid, days=7)

    st.markdown("## 📊 Progress & Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(weekly_study_hours_chart(sessions), use_container_width=True)
    with col2:
        st.plotly_chart(subject_distribution_chart(tasks), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(task_completion_trend(tasks), use_container_width=True)
    with col4:
        st.plotly_chart(priority_breakdown_chart(tasks), use_container_width=True)

    # XP gauge
    st.plotly_chart(
        xp_gauge(st.session_state.xp, st.session_state.level),
        use_container_width=True
    )


def page_achievements():
    uid = st.session_state.user_id
    xp  = st.session_state.xp
    lvl = st.session_state.level
    streak = st.session_state.streak

    st.markdown("## 🏆 Achievements & Badges")

    from rewards import BADGES, LEVEL_TITLES

    # Level & streak
    col1, col2, col3 = st.columns(3)
    col1.metric("⚡ Total XP", xp)
    col2.metric("📊 Level", f"{lvl} — {get_level_title(lvl)}")
    col3.metric("🔥 Streak", f"{streak} days")

    st.markdown("### 🎖️ Badge Collection")
    badge_cols = st.columns(3)
    for i, (threshold, name, desc) in enumerate(BADGES):
        unlocked = xp >= threshold
        with badge_cols[i % 3]:
            opacity = "1" if unlocked else "0.3"
            border  = "rgba(124,58,237,0.8)" if unlocked else "rgba(255,255,255,0.1)"
            st.markdown(f"""
            <div class='sp-card' style='text-align:center;opacity:{opacity};
                 border-color:{border}'>
                <h3 style='font-size:26px;margin:0'>{name}</h3>
                <p style='color:#94A3B8;margin:6px 0;font-size:13px'>{desc}</p>
                <small style='color:#64748B'>Required: {threshold} XP</small>
                {"<br><span class='sp-badge'>✅ Unlocked!</span>" if unlocked else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 🎓 Level Titles")
    lvl_cols = st.columns(4)
    for i, (lv, title) in enumerate(LEVEL_TITLES.items()):
        with lvl_cols[i % 4]:
            current = lv == lvl
            border  = "rgba(6,182,212,0.8)" if current else "rgba(255,255,255,0.1)"
            st.markdown(f"""
            <div class='sp-card' style='text-align:center;border-color:{border}'>
                <p style='font-size:20px;margin:0'>{title}</p>
                <small style='color:#64748B'>Level {lv}</small>
                {"<br><span class='sp-badge'>◀ Current</span>" if current else ""}
            </div>
            """, unsafe_allow_html=True)
def play_alert_sound():
    st.components.v1.html("""
    <script>
    const audio = new Audio("https://www.soundjay.com/misc/sounds/bell-ringing-05.wav");
    audio.play().catch((err) => {
        console.warn('Audio playback failed:', err);
    });
    </script>
    """, height=0)
def show_notification(title="⏰ Time's up!", message="Start your next session!"):
    st.components.v1.html(f"""
    <script>
    // Ask permission
    if (Notification.permission !== "granted") {{
        Notification.requestPermission();
    }}

    // Show notification
    if (Notification.permission === "granted") {{
        new Notification("{title}", {{
            body: "{message}",
            icon: "https://cdn-icons-png.flaticon.com/512/1827/1827392.png"
        }});
    }}

    // Play sound
    var audio = new Audio("https://www.soundjay.com/misc/sounds/bell-ringing-05.wav");
    audio.play();
    </script>
    """, height=0)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not require_login():
        render_auth()
        return

    render_sidebar()

    page = st.session_state.page
    if page == "Dashboard":
        page_dashboard()
    elif page == "Planner":
        render_planner(st.session_state.user_id)
    elif page == "AI Features":
        page_ai_features()
    elif page == "Productivity":
        page_productivity()
    elif page == "Analytics":
        page_analytics()
    elif page == "Voice":
        st.markdown("## 🎙️ Voice Assistant")
        voice_assistant_ui()
    elif page == "Achievements":
        page_achievements()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
    
