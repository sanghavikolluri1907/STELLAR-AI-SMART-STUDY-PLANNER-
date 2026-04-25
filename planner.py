"""
planner.py — Study Planner page: add, view, edit, and complete tasks.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import add_task, get_tasks, complete_task, delete_task, update_task
from rewards import xp_for_task, award_xp


SUBJECTS = [
    "Mathematics", "Physics", "Chemistry", "Biology",
    "English", "History", "Geography", "Computer Science",
    "Economics", "Other",
]

PRIORITY_EMOJI = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
STATUS_EMOJI   = {"Pending": "⏳", "Completed": "✅"}


def render_planner(user_id: int):
    st.markdown("## 📚 Study Planner")

    tab_add, tab_view, tab_edit = st.tabs(["➕ Add Task", "📋 View Tasks", "✏️ Edit Tasks"])

    # ── ADD TASK ──────────────────────────────────────────────────────────
    with tab_add:
        st.markdown("### Add a New Study Task")
        with st.form("add_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                subject = st.selectbox("📖 Subject", SUBJECTS)
                task_name = st.text_input("📝 Task Name", placeholder="e.g. Review Chapter 5")
                priority = st.selectbox("⚡ Priority", ["High", "Medium", "Low"])
            with col2:
                deadline = st.date_input("📅 Deadline", min_value=date.today(),
                                         value=date.today() + timedelta(days=3))
                estimated_hours = st.slider("⏱️ Estimated Hours", 0.5, 8.0, 1.0, step=0.5)
                notes = st.text_area("📌 Notes (optional)", height=68)

            submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

        if submitted:
            if not task_name.strip():
                st.error("Please enter a task name.")
            else:
                add_task(user_id, subject, task_name.strip(), str(deadline), priority, estimated_hours)
                st.success(f"✅ Task **{task_name}** added to {subject}!")
                st.balloons()

    # ── VIEW TASKS ────────────────────────────────────────────────────────
    with tab_view:
        tasks = get_tasks(user_id)

        if not tasks:
            st.info("No tasks yet! Add your first task in the **Add Task** tab.")
            return

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Completed"], key="f_status")
        with col_f2:
            filter_priority = st.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"], key="f_pri")
        with col_f3:
            filter_subject = st.selectbox(
                "Filter by Subject",
                ["All"] + list({t["subject"] for t in tasks}),
                key="f_subj",
            )

        filtered = tasks
        if filter_status != "All":
            filtered = [t for t in filtered if t["status"] == filter_status]
        if filter_priority != "All":
            filtered = [t for t in filtered if t["priority"] == filter_priority]
        if filter_subject != "All":
            filtered = [t for t in filtered if t["subject"] == filter_subject]

        if not filtered:
            st.info("No tasks match the current filters.")
            return

        # Summary metrics
        total = len(filtered)
        done  = sum(1 for t in filtered if t["status"] == "Completed")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", total)
        m2.metric("Completed", done)
        m3.metric("Pending", total - done)
        if total:
            st.progress(done / total)

        # Table view
        df = pd.DataFrame(filtered)
        display_cols = ["subject", "task_name", "deadline", "priority", "status", "estimated_hours"]
        df_show = df[display_cols].rename(columns={
            "subject": "Subject", "task_name": "Task", "deadline": "Deadline",
            "priority": "Priority", "status": "Status", "estimated_hours": "Est. Hours",
        })
        df_show["Priority"] = df_show["Priority"].map(lambda p: f"{PRIORITY_EMOJI.get(p,'')} {p}")
        df_show["Status"]   = df_show["Status"].map(lambda s: f"{STATUS_EMOJI.get(s,'')} {s}")

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # Complete / delete buttons
        st.markdown("---")
        st.markdown("#### ✅ Mark as Completed")
        pending_tasks = [t for t in filtered if t["status"] == "Pending"]
        if pending_tasks:
            task_options = {f"{t['subject']} — {t['task_name']}": t["id"] for t in pending_tasks}
            chosen_label = st.selectbox("Select task to complete", list(task_options.keys()), key="complete_sel")
            if st.button("✅ Mark Complete", use_container_width=True):
                task_id = task_options[chosen_label]
                priority = complete_task(task_id, user_id)
                if priority:
                    xp = xp_for_task(priority)
                    award_xp(user_id, xp)
                    st.session_state.xp = st.session_state.get("xp", 0) + xp
                    st.session_state.level = max(1, st.session_state.xp // 50 + 1)
                    st.success(f"🎉 Task completed! +{xp} XP earned!")
                    st.rerun()
        else:
            st.info("No pending tasks to complete. Great work! 🎉")

        st.markdown("#### 🗑️ Delete Task")
        task_options_del = {f"{t['subject']} — {t['task_name']}": t["id"] for t in filtered}
        del_label = st.selectbox("Select task to delete", list(task_options_del.keys()), key="del_sel")
        if st.button("🗑️ Delete Task", use_container_width=True):
            delete_task(task_options_del[del_label], user_id)
            st.warning("Task deleted.")
            st.rerun()

    # ── EDIT TASKS ────────────────────────────────────────────────────────
    with tab_edit:
        st.markdown("### ✏️ Edit Existing Task")
        tasks = get_tasks(user_id)
        if not tasks:
            st.info("No tasks to edit yet.")
            return

        task_map = {f"[{t['subject']}] {t['task_name']} ({t['deadline']})": t for t in tasks}
        chosen = st.selectbox("Select task to edit", list(task_map.keys()), key="edit_sel")
        t = task_map[chosen]

        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_subject  = st.selectbox("Subject", SUBJECTS, index=SUBJECTS.index(t["subject"]) if t["subject"] in SUBJECTS else 0)
                new_name     = st.text_input("Task Name", value=t["task_name"])
                new_priority = st.selectbox("Priority", ["High", "Medium", "Low"],
                                            index=["High","Medium","Low"].index(t["priority"]))
            with col2:
                new_deadline = st.date_input("Deadline", value=date.fromisoformat(t["deadline"]))
                new_hours    = st.slider("Est. Hours", 0.5, 8.0, float(t.get("estimated_hours") or 1.0), step=0.5)

            save = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if save:
            update_task(t["id"], user_id, new_subject, new_name, str(new_deadline), new_priority, new_hours)
            st.success("✅ Task updated!")
            st.rerun()
