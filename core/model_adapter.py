```python
import streamlit as st
from google import genai


def generate_response(prompt: str) -> str:
    """Generate a response using the configured Gemini model."""

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. "
            "Configure GEMINI_API_KEY in Streamlit Cloud Secrets."
        )

    model = st.secrets.get(
        "GEMINI_MODEL",
        "gemini-3.8-flash",
    )

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    result = interaction.output_text

    if not result:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return result
```
