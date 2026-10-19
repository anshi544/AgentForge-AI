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
    st.markdown(
        """
        <div class="hero">
            <p style="font-size:13px;letter-spacing:2px;">
                YOUR INTELLIGENT WORKSPACE
            </p>
            <h1>Welcome to AgentForge AI</h1>
            <p>
                Turn complex goals into structured workflows using
                specialized AI stages. Plan smarter, execute faster,
                and review every result.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tasks = st.session_state.task_history

    total_tasks = len(tasks)
    completed = sum(
        task.get("status") == "Completed" for task in tasks
    )
    failed = sum(
        task.get("status") == "Failed" for task in tasks
    )
    running = sum(
        task.get("status") == "Running" for task in tasks
    )

    st.markdown("## 📊 Workspace Overview")
    st.caption("A real-time overview of your task history.")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Tasks", total_tasks)

    with c2:
        st.metric("Completed", completed)

    with c3:
        st.metric("In Progress", running)

    with c4:
        st.metric("Failed", failed)

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown("### ⚡ Start Creating")

        st.markdown(
            """
            <div class="agent-card">
                <h4>Build a workflow with AI</h4>
                <p>
                    Describe a goal, choose a workflow type, and let
                    AgentForge AI coordinate planning, execution,
                    and review.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "＋ Create New Task",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.navigation = "Create Task"
            st.rerun()

    with right:
        st.markdown("### 🧠 Your AI Team")

        st.markdown(
            """
            <div class="agent-card">
                <h4>🧭 Planner Agent</h4>
                <p>Structures objectives and plans the workflow.</p>
            </div>
            <div class="agent-card">
                <h4>💻 Specialist Agent</h4>
                <p>Generates the main task output.</p>
            </div>
            <div class="agent-card">
                <h4>✅ Review Agent</h4>
                <p>Reviews the output for completeness and clarity.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🕘 Recent Tasks")

    if not tasks:
        st.info(
            "Your workspace is ready. Create your first task "
            "to see your activity here."
        )
    else:
        for task in tasks[:5]:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{task.get('title', 'Untitled Task')}**")
                    st.caption(
                        f"Workflow: {task.get('type', 'General Task')}"
                    )

                with col2:
                    status = task.get("status", "Unknown")

                    if status == "Completed":
                        st.success(status)
                    elif status == "Failed":
                        st.error(status)
                    else:
                        st.info(status)

                if task.get("result"):
                    with st.expander("View result"):
                        st.markdown(task["result"])

    st.caption(
        "AgentForge AI · Multi-stage AI workflow platform"
    )
elif page == "Create Task":
    st.markdown(
        """
        <div style="
            padding: 28px 30px;
            border-radius: 20px;
            background: linear-gradient(120deg, #101d36, #20204a, #123b50);
            border: 1px solid rgba(103,232,249,0.22);
            margin-bottom: 25px;
        ">
            <div style="
                color: #67e8f9;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 2px;
                margin-bottom: 10px;
            ">AGENTFORGE WORKSPACE</div>
            <h1 style="color: white; margin: 0; font-size: 32px;">
                Create your next workflow
            </h1>
            <p style="
                color: #cbd5e1;
                font-size: 15px;
                margin: 12px 0 0 0;
                line-height: 1.7;
            ">
                Define your goal. Let specialized AI agents plan, execute,
                and review the result.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🛠️ Configure your task")
    st.caption("Provide clear instructions to help the AI agents deliver a useful result.")

    workflow_details = {
        "General Task": (
            "🎯",
            "Flexible workflow",
            "For general questions, problem-solving, and multi-step tasks.",
        ),
        "Research and Report": (
            "🔎",
            "Research workflow",
            "Organize information into a structured report with key findings.",
        ),
        "Coding and Debugging": (
            "💻",
            "Development workflow",
            "Work through programming tasks, code explanations, and debugging.",
        ),
        "Study Planning": (
            "📚",
            "Learning workflow",
            "Create a structured learning plan based on your academic goals.",
        ),
        "Content Creation": (
            "✍️",
            "Creative workflow",
            "Develop structured written content, outlines, and drafts.",
        ),
    }

    with st.form("task_form", clear_on_submit=True):
        title = st.text_input(
            "Task title",
            placeholder="e.g., Create a 30-day Python learning roadmap",
            help="Use a short, descriptive name for your task.",
        )

        description = st.text_area(
            "Describe your objective",
            placeholder=(
                "Explain what you want to achieve...\n\n"
                "Include:\n"
                "• Your goal\n"
                "• Requirements and constraints\n"
                "• Expected output format\n"
                "• Any relevant context"
            ),
            height=190,
            help="Specific instructions generally produce more useful results.",
        )

        st.markdown("#### Select a workflow")

        workflow = st.selectbox(
            "Workflow type",
            list(workflow_details.keys()),
            format_func=lambda name: (
                f"{workflow_details[name][0]}  {name}"
            ),
            help="Choose the workflow that best matches your objective.",
        )

        icon, subtitle, details = workflow_details[workflow]

        st.markdown(
            f"""
            <div style="
                padding: 18px 20px;
                border-radius: 14px;
                background: rgba(103,232,249,0.06);
                border: 1px solid rgba(103,232,249,0.25);
                margin: 8px 0 20px 0;
            ">
                <div style="
                    color: #67e8f9;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 1px;
                ">SELECTED WORKFLOW</div>
                <div style="
                    color: #f1f5f9;
                    font-size: 20px;
                    font-weight: 750;
                    margin-top: 8px;
                ">{icon} {workflow}</div>
                <div style="
                    color: #a5b4fc;
                    font-size: 13px;
                    margin-top: 5px;
                ">{subtitle}</div>
                <div style="
                    color: #cbd5e1;
                    font-size: 14px;
                    margin-top: 9px;
                    line-height: 1.6;
                ">{details}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "🚀 Run Multi-Agent Workflow",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not title.strip() or not description.strip():
            st.error("Please enter both a task title and task description.")
        else:
            task_id = str(uuid.uuid4())

            task = {
                "id": task_id,
                "session_id": st.session_state.session_id,
                "title": title.strip(),
                "description": description.strip(),
                "type": workflow,
                "status": "Running",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
                "error": None,
                "events": [],
            }

            st.session_state.task_history.insert(0, task)
            st.session_state.active_task = task_id

            st.divider()
            st.markdown("### ⚡ Workflow execution")
            st.write(f"**Task:** {task['title']}")
            st.write(f"**Workflow:** {task['type']}")

            progress = st.progress(0, text="Preparing workflow...")
            stage_area = st.status(
                "Initializing AgentForge AI",
                expanded=True,
            )

            try:
                def on_stage(stage_name, message, percent):
                    stage_area.write(f"**{stage_name}**")
                    stage_area.write(message)
                    progress.progress(
                        max(0, min(int(percent), 100)),
                        text=f"{stage_name} · {percent}%",
                    )

                with st.spinner(
                    "AI agents are coordinating your task..."
                ):
                    result, events = run_multi_agent_workflow(
                        title=task["title"],
                        description=task["description"],
                        workflow=task["type"],
                        on_stage=on_stage,
                    )

                task["result"] = result
                task["events"] = events
                task["status"] = "Completed"

                stage_area.update(
                    label="Workflow completed successfully",
                    state="complete",
                    expanded=False,
                )

                progress.progress(100, text="Workflow completed")
                st.success("Task completed and reviewed.")

                st.markdown("### 🤖 Final reviewed result")

                st.markdown(
                    """
                    <div style="
                        padding: 18px;
                        border-radius: 14px;
                        background: rgba(15,23,42,0.45);
                        border: 1px solid rgba(103,232,249,0.2);
                    ">
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(result)

                with st.expander("📋 View agent execution log"):
                    for event in events:
                        st.markdown(
                            f"**{event.get('stage', 'Stage')}** "
                            f"— {event.get('status', 'completed')}"
                        )

                        if event.get("summary"):
                            st.write(event["summary"])

                save_task(task)

            except Exception as exc:
                task["status"] = "Failed"
                task["error"] = str(exc)

                stage_area.update(
                    label="Workflow failed",
                    state="error",
                    expanded=True,
                )

                st.error("The workflow could not be completed.")
                st.caption(f"Error details: {exc}")

                save_task(task)
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
