"""
visualization.py — Plotly chart builders for the Study Planner dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta


COLORS = {
    "primary":   "#7C3AED",
    "secondary": "#3B82F6",
    "accent":    "#06B6D4",
    "success":   "#10B981",
    "warning":   "#F59E0B",
    "danger":    "#EF4444",
    "bg":        "#0F172A",
    "surface":   "#1E293B",
    "text":      "#E2E8F0",
}

SUBJECT_PALETTE = [
    "#7C3AED", "#3B82F6", "#06B6D4", "#10B981",
    "#F59E0B", "#EF4444", "#EC4899", "#8B5CF6",
]


def _dark_layout(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS["text"], size=16)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="Inter, sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text"])),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.1)")
    return fig


def weekly_study_hours_chart(sessions: list[dict]) -> go.Figure:
    """Bar chart: study hours per day for the past 7 days."""
    # Build date range
    today = date.today()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    if not sessions:
        # Empty chart with zero bars
        df = pd.DataFrame({"date": days, "hours": [0] * 7})
    else:
        df_raw = pd.DataFrame(sessions)
        df_raw["hours"] = df_raw["total_min"] / 60
        df_agg = df_raw.groupby("session_date")["hours"].sum().reset_index()
        df_agg.columns = ["date", "hours"]
        df = pd.DataFrame({"date": days}).merge(df_agg, on="date", how="left").fillna(0)

    fig = go.Figure(go.Bar(
        x=df["date"],
        y=df["hours"],
        marker=dict(
            color=df["hours"],
            colorscale=[[0, COLORS["surface"]], [1, COLORS["primary"]]],
            line=dict(width=0),
        ),
        text=[f"{h:.1f}h" for h in df["hours"]],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=11),
    ))
    fig = _dark_layout(fig, "📅 Weekly Study Hours")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Hours")
    return fig


def subject_distribution_chart(tasks: list[dict]) -> go.Figure:
    """Donut chart: task distribution by subject."""
    if not tasks:
        fig = go.Figure()
        return _dark_layout(fig, "📚 Subject Distribution")

    df = pd.DataFrame(tasks)
    counts = df.groupby("subject").size().reset_index(name="count")

    fig = go.Figure(go.Pie(
        labels=counts["subject"],
        values=counts["count"],
        hole=0.55,
        marker=dict(colors=SUBJECT_PALETTE[:len(counts)], line=dict(width=2, color=COLORS["bg"])),
        textinfo="label+percent",
        textfont=dict(color=COLORS["text"], size=12),
    ))
    fig.add_annotation(text="Subjects", x=0.5, y=0.5,
                       font=dict(size=14, color=COLORS["text"]), showarrow=False)
    return _dark_layout(fig, "📚 Subject Distribution")


def task_completion_trend(tasks: list[dict]) -> go.Figure:
    """Line chart: completed vs created tasks over time."""
    if not tasks:
        fig = go.Figure()
        return _dark_layout(fig, "📈 Task Completion Trend")

    df = pd.DataFrame(tasks)
    df["created_date"] = pd.to_datetime(df["created_at"]).dt.date.astype(str)

    created_by_day = df.groupby("created_date").size().reset_index(name="created")

    completed = df[df["status"] == "Completed"].copy()
    if not completed.empty and "completed_at" in completed.columns:
        completed["comp_date"] = pd.to_datetime(
            completed["completed_at"], errors="coerce"
        ).dt.date.astype(str)
        comp_by_day = completed.groupby("comp_date").size().reset_index(name="completed")
    else:
        comp_by_day = pd.DataFrame(columns=["comp_date", "completed"])

    merged = created_by_day.merge(
        comp_by_day, left_on="created_date", right_on="comp_date", how="left"
    ).fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["created_date"], y=merged["created"],
        name="Created", mode="lines+markers",
        line=dict(color=COLORS["secondary"], width=2),
        marker=dict(size=7),
    ))
    fig.add_trace(go.Scatter(
        x=merged["created_date"], y=merged["completed"],
        name="Completed", mode="lines+markers",
        line=dict(color=COLORS["success"], width=2),
        marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.1)",
    ))
    fig = _dark_layout(fig, "📈 Task Completion Trend")
    fig.update_layout(xaxis_title="", yaxis_title="Tasks", legend_orientation="h")
    return fig


def priority_breakdown_chart(tasks: list[dict]) -> go.Figure:
    """Horizontal bar chart: task count by priority and status."""
    if not tasks:
        fig = go.Figure()
        return _dark_layout(fig, "🎯 Priority Breakdown")

    df = pd.DataFrame(tasks)
    pivot = df.groupby(["priority", "status"]).size().unstack(fill_value=0).reset_index()
    priorities = ["High", "Medium", "Low"]
    pivot = pivot[pivot["priority"].isin(priorities)]
    pivot = pivot.set_index("priority").reindex(priorities).fillna(0).reset_index()

    fig = go.Figure()
    if "Pending" in pivot.columns:
        fig.add_trace(go.Bar(
            name="Pending", y=pivot["priority"], x=pivot["Pending"],
            orientation="h", marker_color=COLORS["warning"],
        ))
    if "Completed" in pivot.columns:
        fig.add_trace(go.Bar(
            name="Completed", y=pivot["priority"], x=pivot["Completed"],
            orientation="h", marker_color=COLORS["success"],
        ))
    fig.update_layout(barmode="stack")
    return _dark_layout(fig, "🎯 Priority Breakdown")


def xp_gauge(xp: int, level: int) -> go.Figure:
    """Gauge chart for XP progress."""
    xp_in_level = xp % 50
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=xp_in_level,
        title={"text": f"Level {level} XP Progress", "font": {"color": COLORS["text"], "size": 14}},
        gauge={
            "axis": {"range": [0, 50], "tickcolor": COLORS["text"]},
            "bar": {"color": COLORS["primary"]},
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["surface"],
            "steps": [
                {"range": [0, 25], "color": "rgba(124,58,237,0.2)"},
                {"range": [25, 50], "color": "rgba(124,58,237,0.4)"},
            ],
            "threshold": {
                "line": {"color": COLORS["accent"], "width": 3},
                "thickness": 0.8,
                "value": 50,
            },
        },
        number={"font": {"color": COLORS["text"]}, "suffix": " XP"},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=20, r=20, t=30, b=10),
        height=200,
    )
    return fig
