"""
rewards.py — XP, levels, badges, and gamification helpers.
"""

from database import update_xp, get_user

# XP values
XP_COMPLETE_LOW    = 10
XP_COMPLETE_MEDIUM = 15
XP_COMPLETE_HIGH   = 20
XP_DAILY_LOGIN     = 5
XP_STREAK_BONUS    = 3  # per streak day

# Badge thresholds (XP)
BADGES = [
    (0,   "🥉 Beginner",        "Just getting started!"),
    (50,  "📖 Bookworm",         "50 XP earned — keep reading!"),
    (100, "🎯 Focus Master",     "100 XP — laser-sharp focus!"),
    (200, "⚡ Productivity Pro",  "200 XP — incredible momentum!"),
    (350, "🏆 Study Champion",   "350 XP — you're unstoppable!"),
    (500, "🌟 Knowledge Legend", "500 XP — absolute legend status!"),
]

# Level thresholds: level = xp // 50 + 1
LEVEL_TITLES = {
    1: "🌱 Seedling",
    2: "📗 Learner",
    3: "📘 Scholar",
    4: "📙 Expert",
    5: "📕 Master",
    6: "🎓 Professor",
    7: "🚀 Genius",
    8: "💫 Legend",
}


def xp_for_task(priority: str) -> int:
    mapping = {"High": XP_COMPLETE_HIGH, "Medium": XP_COMPLETE_MEDIUM, "Low": XP_COMPLETE_LOW}
    return mapping.get(priority, XP_COMPLETE_LOW)


def award_xp(user_id: int, xp: int):
    """Add XP to a user and return their updated totals."""
    update_xp(user_id, xp)
    user = get_user_by_id(user_id)
    return user


def get_user_by_id(user_id: int):
    from database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_badge(xp: int) -> tuple[str, str]:
    """Return the highest unlocked badge (name, description)."""
    result = ("🥉 Beginner", "Just getting started!")
    for threshold, name, desc in BADGES:
        if xp >= threshold:
            result = (name, desc)
    return result


def get_level_title(level: int) -> str:
    return LEVEL_TITLES.get(level, LEVEL_TITLES[max(LEVEL_TITLES)])


def xp_to_next_level(xp: int) -> tuple[int, int]:
    """Returns (xp_in_current_level, xp_needed_for_next_level)."""
    xp_per_level = 50
    current_level_xp = xp % xp_per_level
    return current_level_xp, xp_per_level


def streak_bonus_xp(streak: int) -> int:
    """Extra XP for maintaining a streak milestone."""
    if streak % 7 == 0:
        return 25  # weekly bonus
    if streak % 30 == 0:
        return 100  # monthly bonus
    return 0
