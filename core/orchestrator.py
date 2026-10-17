from typing import Callable, Optional

from core.model_adapter import generate_response


WORKFLOW_GUIDANCE = {
    "General Task": "Solve the task clearly and practically.",
    "Research and Report": (
        "Create a research-style report with clear sections. Do not invent citations, "
        "URLs, statistics, or claim that live web research was performed."
    ),
    "Coding and Debugging": (
        "Provide a correct solution, explain the approach, include relevant code, "
        "and discuss important edge cases."
    ),
    "Study Planning": (
        "Create a realistic study plan with daily or weekly topics, time allocations, "
        "practice tasks, revision, and measurable milestones."
    ),
    "Content Creation": (
        "Create polished, well-structured content tailored to the user's requested format."
    ),
}


def _notify(callback, stage, message, percent):
    if callback:
        callback(stage, message, percent)


def run_multi_agent_workflow(
    title: str,
    description: str,
    workflow: str,
    on_stage: Optional[Callable] = None,
):
    """Run sequential planning, specialist-generation, and review model calls."""
    events = []
    guidance = WORKFLOW_GUIDANCE.get(workflow, WORKFLOW_GUIDANCE["General Task"])

    _notify(on_stage, "Planner Agent", "Decomposing the request into objectives.", 10)
    plan_prompt = f"""
You are the Planner Agent in AgentForge AI.
Create a concise but useful execution plan for the task below.
List the objective, key steps, assumptions, constraints, and what a good final
answer must contain. Do not answer the task fully yet.

Task title: {title}
Workflow type: {workflow}
Task description:
{description}
"""
    plan = generate_response(plan_prompt)
    events.append({
        "stage": "Planner Agent",
        "status": "Completed",
        "summary": plan[:1200],
    })

    _notify(on_stage, "Specialist Agent", "Generating the main task output.", 40)
    specialist_prompt = f"""
You are the Specialist Agent in AgentForge AI.
Follow the execution plan and complete the user's task.
Workflow-specific guidance: {guidance}

Important constraints:
- Respect the user's requirements and requested format.
- Do not claim to have executed code, visited websites, or verified facts unless that actually happened.
- State material assumptions where necessary.
- Be concrete and useful rather than generic.

Task title: {title}
Workflow type: {workflow}
Task description:
{description}

Planner's execution plan:
{plan}
"""
    draft = generate_response(specialist_prompt)
    events.append({
        "stage": "Specialist Agent",
        "status": "Completed",
        "summary": draft[:1200],
    })

    _notify(on_stage, "Review Agent", "Checking the draft against the requirements.", 75)
    review_prompt = f"""
You are the Review Agent in AgentForge AI.
Review the draft against the original task and planner's plan.
Fix omissions, contradictions, unsupported claims, unclear wording, and formatting.
Return the improved final answer only. Do not merely list feedback.

Task title: {title}
Workflow type: {workflow}
Original task:
{description}

Plan:
{plan}

Draft to review:
{draft}
"""
    final_result = generate_response(review_prompt)
    events.append({
        "stage": "Review Agent",
        "status": "Completed",
        "summary": final_result[:1200],
    })

    _notify(on_stage, "Workflow Complete", "Final answer reviewed and ready.", 100)
    return final_result, events


# Backwards-compatible function for code that imports execute_task.
def execute_task(title: str, description: str, workflow: str) -> str:
    result, _events = run_multi_agent_workflow(title, description, workflow)
    return result
