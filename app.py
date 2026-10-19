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
        .stApp {
            background: linear-gradient(135deg, #08111f, #101c33);
            color: #f1f5f9;
        }
        .hero {
            padding: 30px;
            border-radius: 18px;
            background: linear-gradient(120deg, #12345a, #155e75);
            border: 1px solid #287b91;
            margin-bottom: 24px;
        }
        .hero h1 { color: #ffffff; font-size: 42px; margin-bottom: 8px; }
        .hero p { color: #dbeafe; font-size: 17px; }
        div[data-testid="stMetric"] {
            background: #142238; border: 1px solid #263b55;
            padding: 18px; border-radius: 14px;
        }
        .agent-card {
            background: #142238; border: 1px solid #263b55;
            border-radius: 14px; padding: 18px; margin-bottom: 12px;
            min-height: 125px;
        }
        .agent-card h4 { color: #67e8f9; margin-top: 0; }
        .section-subtitle { color: #a5b4fc; font-size: 16px; }
        .small-muted { color: #94a3b8; font-size: 13px; }
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
    st.title("🤖 AgentForge AI")
    st.caption("Intelligent Multi-Agent Platform")
    st.divider()

    st.write("👤 Signed in as")
    st.caption(st.session_state.auth_user["email"])

    if st.button("🚪 Log Out", use_container_width=True):
        logout()
        st.session_state.navigation = "Dashboard"
        st.rerun()

    st.divider()

    page = st.radio(
        "Navigation",
        ["Dashboard", "Create Task", "Agent Workspace", "Results", "About"],
        key="navigation",
    )

    st.divider()
    st.caption("⚡ Multi-stage AI task orchestration")
    st.caption("🔧 Gemini model adapter")

    if storage_is_configured():
        st.success("Supabase storage configured")
    else:
        st.info("Session-only storage")

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
            <h1>🤖 AgentForge AI</h1>
            <p>Turn complex goals into structured workflows using coordinated AI stages.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tasks = st.session_state.task_history
    completed = sum(t.get("status") == "Completed" for t in tasks)
    failed = sum(t.get("status") == "Failed" for t in tasks)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tasks Created", len(tasks))
    c2.metric("Workflow Stages", 4)
    c3.metric("Completed", completed)
    c4.metric("Failed", failed)

    st.subheader("Your AI Workspace")
    st.markdown(
        '<p class="section-subtitle">Create tasks, monitor agent stages, and inspect reviewed results.</p>',
        unsafe_allow_html=True,
    )
    if st.button("＋ Create New Task", type="primary"):
        st.session_state.navigation = "Create Task"
        st.rerun()

    st.divider()
    st.subheader("Workflow Agents")
    cols = st.columns(4)
    for i, (name, description) in enumerate(agents):
        with cols[i]:
            st.markdown(
                f'<div class="agent-card"><h4>{name}</h4><p>{description}</p></div>',
                unsafe_allow_html=True,
            )
    st.caption(
        "The workflow performs separate model calls for planning, specialist execution, "
        "and review. These are coordinated stages, not independently hosted agents."
    )

elif page == "Create Task":
    st.title("📝 Create a Task")
    st.write("Describe the outcome you want AgentForge AI to produce.")
    with st.form("task_form", clear_on_submit=True):
        title = st.text_input("Task Title", placeholder="Example: Prepare a Python learning roadmap")
        description = st.text_area(
            "Task Description",
            placeholder="Include your goal, constraints, expected format, and requirements.",
            height=160,
        )
        workflow = st.selectbox(
            "Workflow Type",
            [
                "General Task",
                "Research and Report",
                "Coding and Debugging",
                "Study Planning",
                "Content Creation",
            ],
        )
        submitted = st.form_submit_button("Run Multi-Agent Workflow", type="primary")

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

            progress = st.progress(0, text="Preparing workflow…")
            stage_area = st.status("Starting AgentForge AI workflow", expanded=True)
            try:
                def on_stage(stage_name, message, percent):
                    stage_area.write(f"**{stage_name}:** {message}")
                    progress.progress(percent, text=stage_name)

                with st.spinner("AgentForge AI is coordinating the workflow…"):
                    result, events = run_multi_agent_workflow(
                        title=task["title"],
                        description=task["description"],
                        workflow=task["type"],
                        on_stage=on_stage,
                    )
                task["result"] = result
                task["events"] = events
                task["status"] = "Completed"
                stage_area.update(label="Workflow completed", state="complete", expanded=False)
                progress.progress(100, text="Completed")
                st.success("Task completed and reviewed.")
                st.subheader("🤖 Final Reviewed Result")
                st.markdown(result)
                with st.expander("View agent execution log"):
                    for event in events:
                        st.markdown(f"**{event.get('stage', 'Stage')}** — {event.get('status', '')}")
                        if event.get("summary"):
                            st.write(event["summary"])
                save_task(task)
            except Exception as exc:
                task["status"] = "Failed"
                task["error"] = str(exc)
                stage_area.update(label="Workflow failed", state="error", expanded=True)
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
