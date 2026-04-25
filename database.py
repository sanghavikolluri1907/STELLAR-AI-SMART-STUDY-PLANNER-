"""
database.py — SQLite database initialization and helper functions
"""

import sqlite3
import os

DB_PATH = "study_planner.db"


def get_connection():
    """Return a SQLite connection to the study planner database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they do not exist and seed sample data."""
    conn = get_connection()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            email       TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            last_login  TEXT,
            streak      INTEGER DEFAULT 0,
            last_streak_date TEXT,
            xp          INTEGER DEFAULT 0,
            level       INTEGER DEFAULT 1
        )
    """)

    # ── Tasks ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            subject     TEXT    NOT NULL,
            task_name   TEXT    NOT NULL,
            deadline    TEXT    NOT NULL,
            priority    TEXT    NOT NULL  CHECK(priority IN ('High','Medium','Low')),
            status      TEXT    DEFAULT 'Pending' CHECK(status IN ('Pending','Completed')),
            created_at  TEXT    DEFAULT (datetime('now')),
            completed_at TEXT,
            estimated_hours REAL DEFAULT 1.0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ── Study Sessions ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            subject     TEXT    NOT NULL,
            duration_min INTEGER NOT NULL,
            session_date TEXT   DEFAULT (date('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ── Pomodoro Log ───────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            task_id     INTEGER,
            start_time  TEXT    DEFAULT (datetime('now')),
            completed   INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # ── Daily Goals ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_goals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            goal_date   TEXT    NOT NULL,
            target_hours REAL   DEFAULT 4.0,
            target_tasks INTEGER DEFAULT 3,
            actual_hours REAL   DEFAULT 0.0,
            actual_tasks INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Task CRUD ──────────────────────────────────────────────────────────────────

def add_task(user_id, subject, task_name, deadline, priority, estimated_hours=1.0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO tasks (user_id, subject, task_name, deadline, priority, estimated_hours)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, subject, task_name, deadline, priority, estimated_hours))
    conn.commit()
    conn.close()


def get_tasks(user_id, status=None):
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id=? AND status=? ORDER BY deadline, priority DESC",
            (user_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY deadline, priority DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id, user_id):
    """Mark a task as completed and return its priority for XP calculation."""
    conn = get_connection()
    row = conn.execute(
        "SELECT priority FROM tasks WHERE id=? AND user_id=?",
        (task_id, user_id)
    ).fetchone()
    if row:
        conn.execute("""
            UPDATE tasks
            SET status='Completed', completed_at=datetime('now')
            WHERE id=? AND user_id=?
        """, (task_id, user_id))
        conn.commit()
    conn.close()
    return dict(row)["priority"] if row else None


def delete_task(task_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    conn.close()


def update_task(task_id, user_id, subject, task_name, deadline, priority, estimated_hours):
    conn = get_connection()
    conn.execute("""
        UPDATE tasks
        SET subject=?, task_name=?, deadline=?, priority=?, estimated_hours=?
        WHERE id=? AND user_id=?
    """, (subject, task_name, deadline, priority, estimated_hours, task_id, user_id))
    conn.commit()
    conn.close()


# ── User helpers ───────────────────────────────────────────────────────────────

def get_user(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username, hashed_pw, email=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hashed_pw, email)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success


def update_login(user_id):
    """Update last_login timestamp."""
    conn = get_connection()
    conn.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def update_xp(user_id, xp_gain):
    """Add XP and recalculate level."""
    conn = get_connection()
    row = conn.execute("SELECT xp FROM users WHERE id=?", (user_id,)).fetchone()
    if row:
        new_xp = row["xp"] + xp_gain
        new_level = max(1, new_xp // 50 + 1)
        conn.execute(
            "UPDATE users SET xp=?, level=? WHERE id=?",
            (new_xp, new_level, user_id)
        )
        conn.commit()
    conn.close()


def update_streak(user_id):
    """Increment or reset daily streak; return current streak value."""
    from datetime import date, timedelta
    conn = get_connection()
    row = conn.execute(
        "SELECT streak, last_streak_date FROM users WHERE id=?", (user_id,)
    ).fetchone()
    if not row:
        conn.close()
        return 0
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    streak = row["streak"] or 0
    last = row["last_streak_date"]
    if last == today:
        conn.close()
        return streak
    if last == yesterday:
        streak += 1
    else:
        streak = 1
    conn.execute(
        "UPDATE users SET streak=?, last_streak_date=? WHERE id=?",
        (streak, today, user_id)
    )
    conn.commit()
    conn.close()
    return streak


# ── Study sessions ─────────────────────────────────────────────────────────────

def log_study_session(user_id, subject, duration_min):
    conn = get_connection()
    conn.execute(
        "INSERT INTO study_sessions (user_id, subject, duration_min) VALUES (?,?,?)",
        (user_id, subject, duration_min)
    )
    conn.commit()
    conn.close()


def get_study_sessions(user_id, days=7):
    conn = get_connection()
    rows = conn.execute("""
        SELECT session_date, subject, SUM(duration_min) as total_min
        FROM study_sessions
        WHERE user_id=? AND session_date >= date('now', ?)
        GROUP BY session_date, subject
        ORDER BY session_date
    """, (user_id, f"-{days} days")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Daily goals ────────────────────────────────────────────────────────────────

def upsert_daily_goal(user_id, target_hours, target_tasks):
    from datetime import date
    today = str(date.today())
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM daily_goals WHERE user_id=? AND goal_date=?", (user_id, today)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE daily_goals SET target_hours=?, target_tasks=? WHERE user_id=? AND goal_date=?",
            (target_hours, target_tasks, user_id, today)
        )
    else:
        conn.execute(
            "INSERT INTO daily_goals (user_id, goal_date, target_hours, target_tasks) VALUES (?,?,?,?)",
            (user_id, today, target_hours, target_tasks)
        )
    conn.commit()
    conn.close()


def get_daily_goal(user_id):
    from datetime import date
    today = str(date.today())
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM daily_goals WHERE user_id=? AND goal_date=?", (user_id, today)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
