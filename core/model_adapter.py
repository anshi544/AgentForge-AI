import random
import time

import streamlit as st
from google import genai
from google.genai import errors


MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2
MAX_RETRY_DELAY = 8


def generate_response(prompt: str) -> str:
    """Generate a Gemini response with retries for temporary API failures."""

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. "
            "Add GEMINI_API_KEY to Streamlit Cloud Secrets."
        )

    model = st.secrets.get("GEMINI_MODEL", "gemini-3.8-flash")

    client = genai.Client(api_key=api_key)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            text = getattr(response, "text", None)

            if not text or not text.strip():
                raise RuntimeError(
                    "Gemini returned an empty response. "
                    "Check the model name, API access, and quota."
                )

            return text.strip()

        except errors.APIError as exc:
            status_code = getattr(exc, "code", None)

            # Retry temporary service errors and rate limits.
            retryable = status_code in (429, 500, 502, 503, 504)

            if not retryable:
                raise RuntimeError(
                    f"Gemini API error ({status_code}): {exc}"
                ) from exc

            # Stop after the final attempt.
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(
                    f"Gemini could not complete the request after "
                    f"{MAX_RETRIES} attempts. "
                    f"Last error: {exc}. Please try again later."
                ) from exc

            delay = min(
                INITIAL_RETRY_DELAY * (2 ** attempt),
                MAX_RETRY_DELAY,
            )

            # Add a small random delay to avoid synchronized retries.
            delay += random.uniform(0, 0.5)

            time.sleep(delay)

    raise RuntimeError("Gemini request failed unexpectedly.")
