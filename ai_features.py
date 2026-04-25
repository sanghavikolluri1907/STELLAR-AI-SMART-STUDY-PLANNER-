"""
ai_features.py — AI study suggestions, schedule generation, and motivational tips.
"""

import random
from datetime import date, timedelta


# ── Motivational content ───────────────────────────────────────────────────────

QUOTES = [
    "📚 \"The expert in anything was once a beginner.\" — Helen Hayes",
    "🚀 \"Success is the sum of small efforts repeated day in and day out.\" — Robert Collier",
    "🎯 \"Don't watch the clock; do what it does. Keep going.\" — Sam Levenson",
    "💡 \"Learning never exhausts the mind.\" — Leonardo da Vinci",
    "🔥 \"Push yourself, because no one else is going to do it for you.\"",
    "🌟 \"Great things never come from comfort zones.\"",
    "🏆 \"Believe you can and you're halfway there.\" — Theodore Roosevelt",
    "⚡ \"The secret of getting ahead is getting started.\" — Mark Twain",
    "📖 \"An investment in knowledge pays the best interest.\" — Benjamin Franklin",
    "🎓 \"Education is the most powerful weapon you can use to change the world.\" — Nelson Mandela",
    "💪 \"It does not matter how slowly you go as long as you do not stop.\" — Confucius",
    "🌈 \"Every accomplishment starts with the decision to try.\"",
]

TIPS = [
    "💡 **Tip:** Use the Pomodoro technique — 25 min focus, 5 min break — to maximise productivity.",
    "💡 **Tip:** Review your notes within 24 hours of learning to boost retention by 60%.",
    "💡 **Tip:** Teach a concept to yourself out loud to identify gaps in understanding.",
    "💡 **Tip:** Tackle the hardest subject when your energy is at its peak.",
    "💡 **Tip:** Break large tasks into micro-tasks of 15–20 minutes.",
    "💡 **Tip:** Hydrate! Even mild dehydration reduces cognitive performance by 10%.",
    "💡 **Tip:** Sleep is when your brain consolidates memories — never sacrifice it.",
    "💡 **Tip:** Use spaced repetition: review material at increasing intervals.",
    "💡 **Tip:** Eliminate distractions by silencing notifications during study blocks.",
    "💡 **Tip:** Set a specific outcome for every study session, not just a time block.",
]


def get_random_quote() -> str:
    return random.choice(QUOTES)


def get_tip_of_day() -> str:
    # Deterministic per day so it doesn't change on every rerun
    day_index = date.today().toordinal() % len(TIPS)
    return TIPS[day_index]


# ── Study suggestions ─────────────────────────────────────────────────────────

PRIORITY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}


def sort_tasks_by_urgency(tasks: list[dict]) -> list[dict]:
    """
    Score each pending task by:
      - Days until deadline (closer = higher urgency)
      - Priority weight
    Returns tasks sorted highest urgency first.
    """
    today = date.today()
    scored = []
    for t in tasks:
        try:
            deadline = date.fromisoformat(t["deadline"])
        except (ValueError, TypeError):
            deadline = today + timedelta(days=30)

        days_left = max((deadline - today).days, 0)
        urgency = PRIORITY_WEIGHT.get(t["priority"], 1) * 10 - days_left
        scored.append({**t, "_urgency": urgency, "_days_left": days_left})

    return sorted(scored, key=lambda x: x["_urgency"], reverse=True)


def generate_study_suggestions(tasks: list[dict]) -> list[str]:
    """Return a list of human-readable study suggestion strings."""
    pending = [t for t in tasks if t["status"] == "Pending"]
    if not pending:
        return ["🎉 All tasks are completed! Add new tasks to stay on track."]

    sorted_tasks = sort_tasks_by_urgency(pending)
    suggestions = []
    for i, t in enumerate(sorted_tasks[:5], 1):
        days_left = t["_days_left"]
        if days_left == 0:
            urgency_label = "⚠️ **DUE TODAY**"
        elif days_left == 1:
            urgency_label = "🔴 Due tomorrow"
        elif days_left <= 3:
            urgency_label = f"🟠 {days_left} days left"
        else:
            urgency_label = f"🟢 {days_left} days left"

        suggestions.append(
            f"**{i}. {t['subject']} — {t['task_name']}** | "
            f"{t['priority']} Priority | {urgency_label}"
        )
    return suggestions


# ── Pomodoro schedule generator ────────────────────────────────────────────────

def generate_daily_schedule(tasks: list[dict], start_hour: int = 8) -> list[dict]:
    """
    Assign Pomodoro blocks to pending tasks, starting from start_hour.
    Returns a list of time-block dicts.
    """
    pending = sort_tasks_by_urgency([t for t in tasks if t["status"] == "Pending"])
    if not pending:
        return []

    schedule = []
    current_minutes = start_hour * 60  # minutes since midnight

    for t in pending[:6]:  # cap at 6 tasks per day
        hours = float(t.get("estimated_hours") or 1.0)
        pomodoros = max(1, round(hours * 60 / 25))

        for p in range(pomodoros):
            start_h = current_minutes // 60
            start_m = current_minutes % 60
            end_minutes = current_minutes + 25
            end_h = end_minutes // 60
            end_m = end_minutes % 60

            schedule.append({
                "time": f"{start_h:02d}:{start_m:02d} – {end_h:02d}:{end_m:02d}",
                "subject": t["subject"],
                "task": t["task_name"],
                "type": "🍅 Study",
                "priority": t["priority"],
            })
            current_minutes += 25

            # Add break
            break_start_h = current_minutes // 60
            break_start_m = current_minutes % 60
            break_end = current_minutes + 5
            break_end_h = break_end // 60
            break_end_m = break_end % 60
            schedule.append({
                "time": f"{break_start_h:02d}:{break_start_m:02d} – {break_end_h:02d}:{break_end_m:02d}",
                "subject": "—",
                "task": "Break",
                "type": "☕ Break",
                "priority": "",
            })
            current_minutes += 5

            # Stop if past 10 PM
            if current_minutes >= 22 * 60:
                return schedule

    return schedule


# ── Weak-subject detector ──────────────────────────────────────────────────────

def identify_weak_subjects(tasks: list[dict]) -> list[str]:
    """
    Find subjects where many tasks are still pending relative to total tasks.
    """
    subject_stats: dict[str, dict] = {}
    for t in tasks:
        s = t["subject"]
        subject_stats.setdefault(s, {"total": 0, "pending": 0})
        subject_stats[s]["total"] += 1
        if t["status"] == "Pending":
            subject_stats[s]["pending"] += 1

    weak = []
    for s, stats in subject_stats.items():
        if stats["total"] > 0:
            pct_pending = stats["pending"] / stats["total"]
            if pct_pending >= 0.6:
                weak.append(f"📌 **{s}** — {stats['pending']}/{stats['total']} tasks still pending")
    return weak or ["✅ No weak subjects detected. Great balance!"]
