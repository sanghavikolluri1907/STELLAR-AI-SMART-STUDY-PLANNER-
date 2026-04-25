import streamlit as st

# ── Imports ─────────────────────────
try:
    import speech_recognition as sr
except:
    sr = None

try:
    import pyttsx3
except:
    pyttsx3 = None


# ── Speak Function ─────────────────
def speak(text):
    if pyttsx3:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.say(text)
            engine.runAndWait()
        except:
            pass


# ── Listen Function ────────────────
def listen():
    if not sr:
        return ""

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            st.write("🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        text = recognizer.recognize_google(audio, language="en-IN")
        text = text.lower()

        print("Heard:", text)
        return text

    except:
        return ""


# ── AI RESPONSE ────────────────────
def get_ai_response(text):

    text = text.lower()

    # fix common mistakes
    text = text.replace("sturdy", "study")
    text = text.replace("plane", "plan")

    # ── GREETING ─────────────────
    if "stellar" in text or "hey stellar" in text:
        return "Hi! How can I help you today?"

    if "hello" in text or "hi" in text:
        return "Hello! I'm your study assistant. What do you need help with?"

    # ── STUDY PLAN ──────────────
    if "study" in text and "plan" in text:
        return (
            "Here is a good study plan:\n"
            "- Study 2 to 3 hours daily\n"
            "- Use Pomodoro technique (25 min study + 5 min break)\n"
            "- Focus on weak subjects first\n"
            "- Revise daily before sleep\n"
            "- Practice questions regularly"
        )

    # ── MOTIVATION ──────────────
    if "motivate" in text or "motivation" in text or "lazy" in text or "tired" in text:
        return (
            "Don't give up! 💪\n"
            "- Small progress is still progress\n"
            "- Stay consistent every day\n"
            "- Believe in yourself\n"
            "- Your future depends on today's effort"
        )

    # ── EXAM ────────────────────
    if "exam" in text or "test" in text:
        return (
            "Exam preparation tips:\n"
            "- Revise important topics\n"
            "- Solve previous question papers\n"
            "- Practice daily\n"
            "- Manage your time properly\n"
            "- Stay calm and confident"
        )

    # ── HOW TO STUDY ────────────
    if "how" in text and "study" in text:
        return (
            "Here are some study tips:\n"
            "- Study in short focused sessions\n"
            "- Avoid distractions (mobile, noise)\n"
            "- Take notes while studying\n"
            "- Revise regularly\n"
            "- Practice what you learn"
        )

    # ── TIME MANAGEMENT ─────────
    if "time" in text or "manage time" in text:
        return (
            "Time management tips:\n"
            "- Make a daily schedule\n"
            "- Prioritize important tasks\n"
            "- Avoid procrastination\n"
            "- Use timers while studying\n"
            "- Take proper breaks"
        )

    # ── SUBJECT HELP ────────────
    if "math" in text or "physics" in text or "python" in text:
        return (
            "For subjects:\n"
            "- Understand concepts clearly\n"
            "- Practice problems regularly\n"
            "- Revise formulas\n"
            "- Watch tutorials if needed\n"
            "- Stay consistent"
        )

    # ── HELP ────────────────────
    if "help" in text:
        return (
            "I can help you with:\n"
            "- Study plans\n"
            "- Motivation\n"
            "- Exam preparation\n"
            "- Time management\n"
            "- Study tips\n"
            "- Navigation: go to dashboard, planner, ai features, productivity, analytics, achievements"
        )

    # ── NAVIGATION ──────────────
    if "go to dashboard" in text or "open dashboard" in text or "dashboard" in text:
        st.session_state.page = "Dashboard"
        return "Navigating to Dashboard."

    if "go to planner" in text or "open planner" in text or "planner" in text:
        st.session_state.page = "Planner"
        return "Navigating to Study Planner."

    if "go to ai features" in text or "open ai features" in text or "ai features" in text:
        st.session_state.page = "AI Features"
        return "Navigating to AI Features."

    if "go to productivity" in text or "open productivity" in text or "productivity" in text:
        st.session_state.page = "Productivity"
        return "Navigating to Productivity Tools."

    if "go to analytics" in text or "open analytics" in text or "analytics" in text:
        st.session_state.page = "Analytics"
        return "Navigating to Analytics."

    if "go to achievements" in text or "open achievements" in text or "achievements" in text:
        st.session_state.page = "Achievements"
        return "Navigating to Achievements."

    return "I didn't understand clearly. Try saying study plan, motivation, or exam help."


# ── UI ─────────────────────────────
def voice_assistant_ui():

    st.title("🎤 STELLAR Voice Assistant")

    # 🎤 Voice button
    if st.button("🎤 Speak"):
        text = listen()

        if text:
            st.info(f"🗣️ You said: {text}")
            response = get_ai_response(text)
            speak(response)
            st.success(response)
            if "Navigating" in response:
                st.rerun()
        else:
            st.warning("Couldn't hear properly. Try again.")

    # 💬 Text input
    st.markdown("---")
    text_cmd = st.text_input("Type your command")

    if st.button("Run"):
        if text_cmd:
            response = get_ai_response(text_cmd)
            speak(response)
            st.success(response)
            if "Navigating" in response:
                st.rerun()
            with st.expander("📋 See Available Commands"):
                 
                
              st.markdown("""
- hey stellar  
- give me study plan  
- motivate me  
- exam preparation  
- how to study  
- manage time  
- help  
- go to dashboard  
- go to planner  
- go to ai features  
- go to productivity  
- go to analytics  
- go to achievements  
""")