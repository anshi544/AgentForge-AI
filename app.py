import streamlit as st

# =========================================================

# PAGE CONFIGURATION

# =========================================================

st.set_page_config(
page_title="AgentForge AI",
page_icon="🤖",
layout="wide",
initial_sidebar_state="expanded"
)

# =========================================================

# CUSTOM UI THEME

# =========================================================

st.markdown("""

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

""", unsafe_allow_html=True)

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

```
st.divider()

page_options = [
    "Dashboard",
    "Create Task",
    "Agent Workspace",
    "Results",
    "About"
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
    key="navigation"
)

st.session_state.navigate_to_create = False

st.divider()

st.caption("⚡ AI-powered task orchestration")
st.caption("🔧 Model-independent prototype")
```

# =========================================================

# DASHBOARD

# =========================================================

if page == "Dashboard":

```
st.markdown("""
<div class="hero">
    <h1>🤖 AgentForge AI</h1>
    <p>
        Turn complex goals into structured workflows using
        specialized AI agents.
    </p>
</div>
""", unsafe_allow_html=True)

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
    st.metric(
        "Tasks Created",
        total_tasks
    )

with col2:
    st.metric(
        "Agents Available",
        5
    )

with col3:
    st.metric(
        "Completed Tasks",
        completed_tasks
    )

st.subheader("Your AI Workspace")

st.markdown(
    '<p class="section-subtitle">'
    'Create tasks, organize workflows, and review results.'
    '</p>',
    unsafe_allow_html=True
)

if st.button(
    "＋ Create New Task",
    type="primary",
    use_container_width=False
):
    st.session_state.navigate_to_create = True
    st.rerun()

if pending_tasks:
    st.info(f"You have {pending_tasks} pending task(s).")

st.divider()

st.subheader("Available AI Agents")

agents = [
    (
        "🧭 Planner Agent",
        "Breaks complex goals into smaller, manageable tasks."
    ),
    (
        "🔎 Research Agent",
        "Organizes information relevant to the requested task."
    ),
    (
        "📊 Analyst Agent",
        "Examines findings and identifies important insights."
    ),
    (
        "✍️ Writer Agent",
        "Produces structured content based on task requirements."
    ),
    (
        "✅ Review Agent",
        "Checks outputs against the user's requirements."
    )
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
            unsafe_allow_html=True
        )

st.caption(
    "Note: The agents are currently represented in the UI. "
    "AI execution will be integrated in a later development stage."
)
```

# =========================================================

# CREATE TASK

# =========================================================

elif page == "Create Task":

```
st.title("📝 Create a Task")

st.write(
    "Describe the goal you want AgentForge AI to accomplish."
)

with st.form("task_form", clear_on_submit=True):

    task_title = st.text_input(
        "Task Title",
        placeholder="Example: Prepare a Python learning roadmap"
    )

    task_description = st.text_area(
        "Describe Your Goal",
        placeholder=(
            "Explain what you want to accomplish, "
            "the expected result, and any requirements."
        ),
        height=160
    )

    task_type = st.selectbox(
        "Workflow Type",
        [
            "General Task",
            "Research and Report",
            "Coding and Debugging",
            "Study Planning",
            "Content Creation"
        ]
    )

    submitted = st.form_submit_button(
        "Create Task",
        type="primary"
    )

if submitted:

    if not task_title.strip() or not task_description.strip():

        st.error(
            "Please enter both a task title and task description."
        )

    else:

        task = {
            "id": (
                max(
                    (
                        item["id"]
                        for item in st.session_state.task_history
                    ),
                    default=0
                ) + 1
            ),
            "title": task_title.strip(),
            "description": task_description.strip(),
            "type": task_type,
            "status": "Pending",
            "result": None
        }

        st.session_state.task_history.append(task)
        st.session_state.active_task = task["id"]

        st.success("Task created successfully!")

       st.info(
"Your task has been saved in the current session. "
"Automated agent execution has not been connected yet."
)

```
