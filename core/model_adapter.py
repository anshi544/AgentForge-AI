import streamlit as st
from google import genai


def generate_response(prompt: str) -> str:
    """Generate an AI response using the configured Gemini provider."""

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Configure GEMINI_API_KEY "
            "in Streamlit Cloud Secrets."
        )

    model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("The AI provider returned an empty response.")

    return response.text
