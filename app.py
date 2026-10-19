import uuid
from datetime import datetime, timezone

import streamlit as st

from core.orchestrator import run_multi_agent_workflow
from core.storage import save_task, load_tasks, storage_is_configured
from core.auth import (
    init_auth_state,
    get_authenticated_client,
    show_auth_page,
    logout,
)

st.set_page_config(
    page_title="AgentForge AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        /* Main application background */
        .stApp {
            background:
                radial-gradient(
                    ellipse at top left,
                    rgba(14, 116, 144, 0.18),
                    transparent 40%
                ),
                linear-gradient(135deg, #07111f, #0c1729 55%, #101c33);
            color: #f1f5f9;
        }

        /* Main content spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        /* Hero section */
        .hero {
            padding: 38px;
            border-radius: 24px;
            background:
                linear-gradient(
                    120deg,
                    rgba(30, 64, 110, 0.96),
                    rgba(8, 145, 178, 0.75)
                );
            border: 1px solid rgba(103, 232, 249, 0.3);
            margin-bottom: 28px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
        }

        .hero h1 {
            color: #ffffff;
            font-size: clamp(30px, 4vw, 46px);
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 12px;
        }

        .hero p {
            color: #e0f2fe;
            font-size: 17px;
            line-height: 1.7;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #14263e, #101e32);
            border: 1px solid #263e59;
            padding: 22px;
            border-radius: 18px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transition: border-color 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            border-color: #22d3ee;
        }

        div[data-testid="stMetricLabel"] {
            color: #a5b4fc;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
            font-weight: 750;
        }

        /* Workflow agent cards */
        .agent-card {
            background: linear-gradient(145deg, #14263e, #101e32);
            border: 1px solid #263e59;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 14px;
            min-height: 145px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transition:
                transform 0.2s ease,
                border-color 0.2s ease;
        }

        .agent-card:hover {
            transform: translateY(-3px);
            border-color: #22d3ee;
        }

        .agent-card h4 {
            color: #67e8f9;
            margin-top: 0;
            font-size: 17px;
        }

        .agent-card p {
            color: #cbd5e1;
            line-height: 1.6;
            font-size: 14px;
        }

        /* Section descriptions */
        .section-subtitle {
            color: #a5b4fc;
            font-size: 16px;
            line-height: 1.7;
        }

        .small-muted {
            color: #94a3b8;
            font-size: 13px;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1627, #0d1b30);
            border-right: 1px solid #20344d;
        }

        section[data-testid="stSidebar"] h1 {
            color: #67e8f9;
            font-weight: 800;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 11px;
            font-weight: 650;
            min-height: 42px;
            transition: all 0.2s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: #22d3ee;
            color: #67e8f9;
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea {
            background-color: #101e32;
            color: #f1f5f9;
            border-radius: 10px;
            border-color: #344a65;
        }

        /* Select boxes */
        div[data-baseweb="select"] > div {
            background-color: #101e32;
            border-color: #344a65;
            border-radius: 10px;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            background: rgba(20, 34, 56, 0.55);
            border: 1px solid #263b55;
            border-radius: 14px;
        }

        /* Progress bars */
        div[data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #0891b2, #67e8f9);
        }

        /* Separators */
        hr {
            border-color: #263b55;
        }

        /* Mobile adjustments */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero {
                padding: 24px;
                border-radius: 18px;
            }

            .hero h1 {
                font-size: 30px;
            }

            .agent-card {
                min-height: auto;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)
# Initialize authentication state.
init_auth_state()

# Require authentication before displaying the workspace.
authenticated_client = get_authenticated_client()

if authenticated_client is None:
    show_auth_page()
    st.stop()

# Initialize task state for the authenticated user.
user = st.session_state.auth_user
st.session_state.session_id = user["id"]

if "task_history" not in st.session_state:
    st.session_state.task_history = load_tasks()

if "active_task" not in st.session_state:
    st.session_state.active_task = None

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 12px 0 20px 0;">
            <div style="
                font-size: 30px;
                font-weight: 850;
                background: linear-gradient(90deg, #67e8f9, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            ">
                🤖 AgentForge
            </div>
            <div style="
                color: #94a3b8;
                font-size: 12px;
                letter-spacing: 1.5px;
                margin-top: 5px;
            ">
                INTELLIGENT AI WORKSPACE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("##### ACCOUNT")

    st.write("👤 Signed in as")
    st.caption(st.session_state.auth_user["email"])

    if st.button("🚪 Log Out", use_container_width=True):
        logout()
        st.session_state.navigation = "Dashboard"
        st.rerun()

    st.divider()

    st.markdown("##### WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Create Task",
            "Agent Workspace",
            "Results",
            "About",
        ],
        key="navigation",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("##### SYSTEM STATUS")

    st.caption("⚡ Multi-stage AI orchestration")
    st.caption("🧠 Gemini AI integration")

    if storage_is_configured():
        st.success("Supabase configured")
    else:
        st.warning("Session-only storage")

    st.markdown(
        """
        <div style="
            padding-top: 20px;
            color: #64748b;
            font-size: 11px;
            text-align: center;
        ">
            AGENTFORGE AI · 2026
        </div>
        """,
        unsafe_allow_html=True,
    )

agents = [
    ("🧭 Planner Agent", "Decomposes the request into clear objectives."),
    ("🔎 Research Agent", "Builds evidence-oriented research outputs."),
    ("💻 Specialist Agent", "Executes the selected workflow instructions."),
    ("✅ Review Agent", "Reviews the draft against the user's requirements."),
]

if page == "Dashboard":
    import pandas as pd

    st.title("📊 Analytics Dashboard")
    st.caption(
        "Monitor task execution, workflow distribution, "
        "and workspace activity."
    )

    tasks = st.session_state.task_history

    # Calculate task statistics
    total_tasks = len(tasks)

    completed = sum(
        task.get("status") == "Completed"
        for task in tasks
    )

    failed = sum(
        task.get("status") == "Failed"
        for task in tasks
    )

    running = sum(
        task.get("status") == "Running"
        for task in tasks
    )

    completion_rate = (
        round((completed / total_tasks) * 100, 1)
        if total_tasks > 0
        else 0
    )

    # KPI cards
    st.subheader("Workspace Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Tasks",
            value=total_tasks,
        )

    with col2:
        st.metric(
            label="Completed",
            value=completed,
        )

    with col3:
        st.metric(
            label="Failed",
            value=failed,
        )

    with col4:
        st.metric(
            label="Completion Rate",
            value=f"{completion_rate}%",
        )

    st.divider()

    if not tasks:
        st.info(
            "Your analytics will appear here after you create "
            "your first task."
        )

        if st.button(
            "＋ Create Your First Task",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.navigation = "Create Task"
            st.rerun()

    else:
        # Prepare chart data
        status_data = pd.DataFrame({
            "Status": [
                "Completed",
                "Running",
                "Failed",
            ],
            "Tasks": [
                completed,
                running,
                failed,
            ],
        })

        workflow_counts = {}

        for task in tasks:
            workflow = task.get(
                "type",
                "General Task",
            )

            workflow_counts[workflow] = (
                workflow_counts.get(workflow, 0) + 1
            )

        workflow_data = pd.DataFrame({
            "Workflow": list(workflow_counts.keys()),
            "Tasks": list(workflow_counts.values()),
        })

        # Analytics charts
        st.subheader("Task Analytics")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### Task Status Distribution")

            st.bar_chart(
                status_data.set_index("Status"),
                y="Tasks",
                use_container_width=True,
            )

            st.caption(
                "Number of tasks in each execution state."
            )

        with chart_col2:
            st.markdown("#### Workflow Distribution")

            st.bar_chart(
                workflow_data.set_index("Workflow"),
                y="Tasks",
                use_container_width=True,
            )

            st.caption(
                "Number of tasks created for each workflow type."
            )

        st.divider()

        # Recent activity
        st.subheader("🕒 Recent Task Activity")

        activity_rows = []

        for task in tasks[:20]:
            activity_rows.append({
                "Task": task.get(
                    "title",
                    "Untitled Task",
                ),
                "Workflow": task.get(
                    "type",
                    "General Task",
                ),
                "Status": task.get(
                    "status",
                    "Unknown",
                ),
                "Created At": task.get(
                    "created_at",
                    "Unknown",
                ),
            })

        activity_df = pd.DataFrame(activity_rows)

        st.dataframe(
            activity_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Showing up to 20 recent tasks from your workspace."
        )

        st.divider()

        # Quick action
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button(
                "＋ Create New Task",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.navigation = "Create Task"
                st.rerun()

        with action_col2:
            if st.button(
                "📂 View All Results",
                use_container_width=True,
            ):
                st.session_state.navigation = "Results"
                st.rerun()
elif page == "Agent Workspace":
    st.title("🧠 Agent Workspace")
    st.write("Review the stages used by the current orchestration workflow.")
    descriptions = [
        ("Planner Agent", "Creates a structured plan and identifies subtasks."),
        ("Research Agent", "For research workflows, produces a research-focused draft. It does not independently browse the web unless web search is separately integrated."),
        ("Specialist Agent", "Generates the main output according to the selected workflow."),
        ("Review Agent", "Checks completeness, clarity, consistency, and requested format."),
    ]
    for name, description in descriptions:
        with st.expander(name):
            st.write(description)
            st.caption("Runs as a distinct stage in the multi-call workflow.")

    st.divider()
    st.subheader("Recent Tasks")
    if not st.session_state.task_history:
        st.info("No tasks yet. Create a task to populate your workspace.")
    else:
        for task in st.session_state.task_history[:10]:
            with st.container(border=True):
                st.write(f"**{task['title']}**")
                st.write(f"Workflow: {task['type']} · Status: {task['status']}")
                st.caption(f"Task ID: {task['id']}")

elif page == "Results":
    st.title("📊 Task Results")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.write("View your completed and previously saved tasks.")

    with col2:
        if st.button("🔄 Refresh History"):
            saved_tasks = load_tasks()

            if saved_tasks:
                st.session_state.task_history = saved_tasks
                st.success("Task history refreshed.")
            else:
                st.info("No saved tasks found for this session.")

    tasks = st.session_state.task_history

    if not tasks:
        st.info("No tasks available. Create a task first.")
    else:
        for task in tasks:
            with st.expander(
                f"{task['title']} · {task['status']}",
                expanded=False,
            ):
                st.write(
                    "**Workflow:**",
                    task.get("type", "General Task"),
                )
                st.write(
                    "**Created:**",
                    task.get("created_at", "Unknown"),
                )

                st.write("**Description:**")
                st.write(task.get("description", ""))

                if task.get("result"):
                    st.subheader("Final Reviewed Result")
                    st.markdown(task["result"])

                if task.get("error"):
                    st.error(task["error"])

                events = task.get("events", [])

                if events:
                    st.subheader("Execution Log")

                    for event in events:
                        st.markdown(
                            f"- **{event.get('stage', 'Stage')}** — "
                            f"{event.get('status', 'completed')}: "
                            f"{event.get('summary', '')}"
                        )

elif page == "About":
    st.title("ℹ️ About AgentForge AI")
    st.markdown(
        """
        AgentForge AI coordinates multiple AI workflow stages to turn a user request
        into a planned, generated, and reviewed result.

        **Included in this upgrade**
        - Planner, specialist, and review model stages
        - Per-stage progress and execution log
        - Task result history
        - Optional Supabase persistence
        - Gemini model configuration through Streamlit Secrets

        **Current limitations**
        - The stages are sequential model calls, not separate autonomous services.
        - Research tasks do not automatically browse the web or verify external sources.
        - Without Supabase credentials and the SQL setup, task history is session-only.
        - Public deployments should add user authentication before storing private user data.
        """
    )
    st.caption("AgentForge AI | Multi-stage AI workflow prototype")
