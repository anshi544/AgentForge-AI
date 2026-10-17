import streamlit as st
from core.orchestrator import execute_task
# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AgentForge AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM UI THEME
# =========================================================

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
        .hero h1 {
            color: #ffffff;
            font-size: 42px;
            margin-bottom: 8px;
        }
        .hero p {
            color: #dbeafe;
            font-size: 17px;
        }
        div[data-testid="stMetric"] {
            background: #142238;
            border: 1px solid #263b55;
            padding: 18px;
            border-radius: 14px;
        }
        .agent-card {
            background: #142238;
            border: 1px solid #263b55;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 12px;
            min-height: 125px;
        }
        .agent-card h4 {
            color: #67e8f9;
            margin-top: 0;
        }
        .section-subtitle {
            color: #a5b4fc;
            font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "active_task" not in st.session_state:
    st.session_state.active_task = None

if "navigate_to_create" not in st.session_state:
    st.session_state.navigate_to_create = False

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:
    st.title("🤖 AgentForge AI")
    st.caption("Intelligent Multi-Agent Platform")
    st.divider()

    page_options = [
        "Dashboard",
        "Create Task",
        "Agent Workspace",
        "Results",
        "About",
    ]

    default_page_index = (
        page_options.index("Create Task")
        if st.session_state.navigate_to_create
        else 0
    )

    page = st.radio(
        "Navigation",
        page_options,
        index=default_page_index,
        key="navigation",
    )

    st.session_state.navigate_to_create = False
    st.divider()
    st.caption("⚡ AI-powered task orchestration")
    st.caption("🔧 Model-independent prototype")

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":
    st.markdown(
        """
        <div class="hero">
            <h1>🤖 AgentForge AI</h1>
            <p>
                Turn complex goals into structured workflows
                using specialized AI agents.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_tasks = len(st.session_state.task_history)
    completed_tasks = sum(
        task["status"] == "Completed"
        for task in st.session_state.task_history
    )
    pending_tasks = sum(
        task["status"] == "Pending"
        for task in st.session_state.task_history
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Tasks Created", total_tasks)
    with col2:
        st.metric("Agents Available", 5)
    with col3:
        st.metric("Completed Tasks", completed_tasks)

    st.subheader("Your AI Workspace")
    st.markdown(
        '<p class="section-subtitle">'
        "Create tasks, organize workflows, and review results."
        "</p>",
        unsafe_allow_html=True,
    )

    if st.button("＋ Create New Task", type="primary"):
        st.session_state.navigate_to_create = True
        st.rerun()

    if pending_tasks:
        st.info(f"You have {pending_tasks} pending task(s).")

    st.divider()
    st.subheader("Available AI Agents")

    agents = [
        (
            "🧭 Planner Agent",
            "Breaks complex goals into smaller, manageable tasks.",
        ),
        (
            "🔎 Research Agent",
            "Organizes information relevant to the requested task.",
        ),
        (
            "📊 Analyst Agent",
            "Examines findings and identifies important insights.",
        ),
        (
            "✍️ Writer Agent",
            "Produces structured content based on task requirements.",
        ),
        (
            "✅ Review Agent",
            "Checks outputs against the user's requirements.",
        ),
    ]

    columns = st.columns(3)
    for index, (name, description) in enumerate(agents):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="agent-card">
                    <h4>{name}</h4>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(
        "Prototype status: Agents are represented in the interface. "
        "AI execution has not yet been integrated."
    )

# =========================================================
# CREATE TASK
# =========================================================

elif page == "Create Task":
    st.title("📝 Create a Task")
    st.write("Describe the goal you want AgentForge AI to accomplish.")

    with st.form("task_form", clear_on_submit=True):
        task_title = st.text_input(
            "Task Title",
            placeholder="Example: Prepare a Python learning roadmap",
        )

        task_description = st.text_area(
            "Describe Your Goal",
            placeholder=(
                "Explain what you want to accomplish, "
                "the expected result, and any requirements."
            ),
            height=160,
        )

        task_type = st.selectbox(
            "Workflow Type",
            [
                "General Task",
                "Research and Report",
                "Coding and Debugging",
                "Study Planning",
                "Content Creation",
            ],
        )

        submitted = st.form_submit_button(
            "Create Task",
            type="primary",
        )

    if submitted:
        if not task_title.strip() or not task_description.strip():
            st.error(
                "Please enter both a task title and task description."
            )
        else:
            task = {
                "id": max(
                    (
                        item["id"]
                        for item in st.session_state.task_history
                    ),
                    default=0,
                ) + 1,
                "title": task_title.strip(),
                "description": task_description.strip(),
                "type": task_type,
                "status": "Running",
                "result": None,
                "error": None,
            }

            st.session_state.task_history.append(task)
            st.session_state.active_task = task["id"]

            try:
                with st.spinner(
                    "AgentForge AI is processing your task..."
                ):
                    result = execute_task(
                        title=task["title"],
                        description=task["description"],
                        workflow=task["type"],
                    )

                task["result"] = result
                task["status"] = "Completed"

                st.success("Task completed successfully!")
                st.subheader("🤖 AI-Generated Result")
                st.markdown(result)

            except Exception as e:
                task["status"] = "Failed"
                task["error"] = str(e)

                st.error(
                    "The task could not be completed. "
                    "Check your API configuration and deployment logs."
                )
                st.caption(f"Error details: {e}")
# =========================================================
# AGENT WORKSPACE
# =========================================================

elif page == "Agent Workspace":
    st.title("🧠 Agent Workspace")
    st.write(
        "Review the available agents and the tasks waiting in your queue."
    )

    workspace_agents = [
        ("🧭 Planner Agent", "Plans and decomposes tasks."),
        ("🔎 Research Agent", "Organizes research requirements."),
        ("📊 Analyst Agent", "Analyzes information and findings."),
        ("✍️ Writer Agent", "Structures content and reports."),
        ("✅ Review Agent", "Checks output quality and requirements."),
    ]

    for name, description in workspace_agents:
        with st.expander(name):
            st.write(description)
            st.caption("Status: Awaiting AI execution integration")

    st.divider()
    st.subheader("Task Queue")

    if not st.session_state.task_history:
        st.info("No tasks yet. Create a task to populate your workspace.")
    else:
        for task in st.session_state.task_history:
            with st.container(border=True):
                st.write(f"**{task['title']}**")
                st.write(f"Task ID: {task['id']}")
                st.write(f"Workflow: {task['type']}")
                st.write(f"Status: {task['status']}")

# =========================================================
# RESULTS
# =========================================================

elif page == "Results":
    st.title("📊 Task Results")

    if not st.session_state.task_history:
        st.info("No tasks available. Create a task first.")
    else:
        for task in reversed(st.session_state.task_history):
            with st.expander(f"Task {task['id']}: {task['title']}"):
                st.write("**Description:**")
                st.write(task["description"])
                st.write("**Workflow:**", task["type"])
                st.write("**Status:**", task["status"])

                if task["result"]:
    st.subheader("🤖 AI-Generated Result")
    st.markdown(task["result"])
else:
    st.info("No result is available for this task yet.")

elif task.get("error"):
    st.error("Task execution failed.")
    st.caption(task["error"])

else:
    st.info(
        "No result is available for this task yet."
    )

# =========================================================
# ABOUT
# =========================================================

elif page == "About":
    st.title("ℹ️ About AgentForge AI")
    st.markdown(
        """
        AgentForge AI is a model-independent multi-agent platform
        prototype designed to organize complex tasks into structured
        workflows.

        **Current features**
        - Interactive dashboard and task metrics
        - Task creation with descriptions and workflow categories
        - Agent workspace with five specialized agent roles
        - Task queue and results interface

        **Current limitations**
        - Tasks are stored in Streamlit session state.
        - Tasks may disappear when the session resets.
        - AI models and automated agent execution are not connected.
        - Results are not generated automatically.

        **Planned development**
        - Integrate an AI model provider
        - Implement agent orchestration and task execution
        - Add persistent storage
        - Display generated results and execution status
        """
    )
    st.caption("AgentForge AI | Multi-Agent Platform Prototype")
