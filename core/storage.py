import streamlit as st

from core.auth import get_authenticated_client


def storage_is_configured() -> bool:
    """Check whether Supabase credentials are configured."""
    try:
        return bool(
            st.secrets.get("SUPABASE_URL")
            and st.secrets.get("SUPABASE_KEY")
        )
    except Exception:
        return False


def save_task(task: dict) -> bool:
    """Save a task for the currently authenticated user."""
    client = get_authenticated_client()

    if client is None:
        st.warning("Log in to save tasks to your account.")
        return False

    user = st.session_state.auth_user

    record = {
        "id": task["id"],
        "session_id": st.session_state.session_id,
        "user_id": user["id"],
        "title": task["title"],
        "description": task["description"],
        "workflow": task["type"],
        "status": task["status"],
        "result": task.get("result"),
        "error": task.get("error"),
        "events": task.get("events", []),
        "created_at": task.get("created_at"),
    }

    try:
        client.table("agentforge_tasks").upsert(record).execute()
        return True
    except Exception as exc:
        st.error(f"Task ran, but saving failed: {exc}")
        return False


def load_tasks(session_id: str = None) -> list:
    """Load tasks belonging only to the authenticated user."""
    client = get_authenticated_client()

    if client is None:
        return []

    user = st.session_state.auth_user

    try:
        query = (
            client.table("agentforge_tasks")
            .select("*")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(50)
        )

        response = query.execute()
        rows = response.data or []

        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "title": row["title"],
                "description": row["description"],
                "type": row["workflow"],
                "status": row["status"],
                "result": row.get("result"),
                "error": row.get("error"),
                "events": row.get("events") or [],
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]

    except Exception as exc:
        st.error(f"Unable to load saved tasks: {exc}")
        return []
