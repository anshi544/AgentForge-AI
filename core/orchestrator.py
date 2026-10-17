from core.model_adapter import generate_response


def execute_task(title: str, description: str, workflow: str) -> str:
    """Route a task through a simple AI workflow."""

    instructions = {
        "General Task": (
            "Solve the user's task clearly and step by step."
        ),
        "Research and Report": (
            "Prepare a structured research-style response. "
            "Do not invent sources or claim that web research was performed."
        ),
        "Coding and Debugging": (
            "Provide a suitable coding solution, explain it, "
            "and include relevant error handling."
        ),
        "Study Planning": (
            "Create a practical study plan with topics, time allocations, "
            "practice activities, and milestones."
        ),
        "Content Creation": (
            "Create polished, well-organized content that meets "
            "the user's requirements."
        ),
    }

    task_instruction = instructions.get(
        workflow,
        instructions["General Task"],
    )

    prompt = f"""
You are AgentForge AI, an AI task-assistance platform.

WORKFLOW:
{workflow}

INSTRUCTIONS:
{task_instruction}

TASK TITLE:
{title}

TASK DESCRIPTION:
{description}

REQUIREMENTS:
- Be accurate and specific.
- Organize the answer using headings and lists where useful.
- State limitations when information is uncertain.
- Do not claim to have performed actions you did not perform.

Provide the completed response below.
"""

    return generate_response(prompt)
