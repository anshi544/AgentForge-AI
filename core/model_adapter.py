import streamlit as st
from google import genai


def generate_response(prompt: str) -> str:
    """Call the configured Gemini model and return plain text."""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Add GEMINI_API_KEY to Streamlit Cloud Secrets."
        )

    model = st.secrets.get("GEMINI_MODEL", "gemini-3.8-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise RuntimeError(
            "Gemini returned an empty response. Check the model name, API access, and quota."
        )
    return text.strip()
