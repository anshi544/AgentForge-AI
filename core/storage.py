import streamlit as st
from supabase import create_client


def storage_is_configured() -> bool:
    try:
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False


def _client():
    if not storage_is_configured():
        return None
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def save_task(task: dict) -> None:
    """Persist a task if Supabase is configured; otherwise keep it in session state."""
    client = _client()
    if client is None:
        return
    record = {
        "id": task["id"],
        "session_id": task["session_id"],
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
    except Exception as exc:
        # Don't hide the task result if persistence is temporarily unavailable.
        st.warning(f"Task ran, but saving to Supabase failed: {exc}")


def load_tasks(session_id: str) -> list:
    """Load tasks for this browser session when Supabase is configured."""
    client = _client()
    if client is None:
        return []
    try:
        response = (
            client.table("agentforge_tasks")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
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
    except Exception:
        # Missing table / credentials should not prevent the app from starting.
        return []
