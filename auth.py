"""
auth.py — Registration, login, and session helpers using bcrypt.
"""

import bcrypt
import streamlit as st
from database import create_user, get_user, update_login, update_streak, update_xp


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Auth actions ──────────────────────────────────────────────────────────────

def register_user(username: str, password: str, email: str = "") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    hashed = hash_password(password)
    if create_user(username.strip().lower(), hashed, email):
        return True, "✅ Account created! Please log in."
    return False, "❌ Username already taken. Try another."


def login_user(username: str, password: str) -> tuple[bool, str]:
    """Authenticate user and populate st.session_state. Returns (success, message)."""
    user = get_user(username.strip().lower())
    if not user:
        return False, "❌ User not found."
    if not verify_password(password, user["password"]):
        return False, "❌ Incorrect password."

    # Update DB
    update_login(user["id"])
    streak = update_streak(user["id"])
    xp_gain = 5  # daily login bonus
    update_xp(user["id"], xp_gain)

    # Re-fetch updated user
    user = get_user(username.strip().lower())

    # Populate session
    st.session_state.logged_in = True
    st.session_state.user_id   = user["id"]
    st.session_state.username  = user["username"]
    st.session_state.xp        = user["xp"]
    st.session_state.level     = user["level"]
    st.session_state.streak    = streak

    return True, f"✅ Welcome back, **{user['username']}**! 🔥 Streak: {streak} days"


def logout_user():
    """Clear session state."""
    for key in ["logged_in", "user_id", "username", "xp", "level", "streak"]:
        st.session_state.pop(key, None)


def require_login():
    """Return True if a user is logged in, else False."""
    return st.session_state.get("logged_in", False)
