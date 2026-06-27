"""LLM analyzer for broken Python code and pytest failures."""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

_GEMINI_API_KEY: Final[str | None] = os.getenv("GEMINI_API_KEY")
if _GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _GEMINI_API_KEY

client: Final[genai.Client] = genai.Client()
MODEL_NAME: Final[str] = "gemini-2.5-flash"
SYSTEM_MESSAGE: Final[str] = (
    "You are an Expert Debugging Agent. Your job is to analyze broken Python code "
    "and the resulting pytest stack trace to explain exactly why it failed."
)


def analyze_error(current_code: str, error_output: str) -> str:
    """Analyze broken Python code and pytest error output.

    Args:
        current_code: The current source code that failed.
        error_output: The pytest stack trace or failure output.

    Returns:
        The LLM's analysis as a string.

    Raises:
        RuntimeError: If the Gemini request fails or returns no content.
    """

    if not _GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set.")

    user_message = (
        "Current code:\n"
        "```python\n"
        f"{current_code}\n"
        "```\n\n"
        "Pytest error output:\n"
        "```text\n"
        f"{error_output}\n"
        "```"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config={"system_instruction": SYSTEM_MESSAGE},
        )
    except APIError as exc:
        raise RuntimeError(f"Gemini analysis request failed: {exc}") from exc

    content = response.text
    if content is None:
        raise RuntimeError("Gemini returned an empty response.")

    return content


if __name__ == "__main__":
    demo_code = """def divide(a, b):
    return a / b

print(divide(1, 0))
"""
    mock_trace = """Traceback (most recent call last):
  File "demo.py", line 4, in <module>
    print(divide(1, 0))
  File "demo.py", line 2, in divide:
    return a / b
ZeroDivisionError: division by zero
"""

    try:
        print(analyze_error(demo_code, mock_trace))
    except RuntimeError as exc:
        print(exc)
