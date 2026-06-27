"""Structured patch generation and application utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from rich.console import Console

load_dotenv()

client: Final[genai.Client] = genai.Client()
MODEL_NAME: Final[str] = "gemini-2.5-flash"
SYSTEM_MESSAGE: Final[str] = (
    "You are an Expert Debugging Agent. Your job is to analyze broken Python code "
    "and produce a full-file patch that fixes the bug. Return only structured "
    "output matching the requested schema."
)
console: Final[Console] = Console()


class AgentPatch(BaseModel):
    """Structured patch returned by the model."""

    thought_process: str = Field(
        ..., description="Explain the root cause of the bug and how the fix addresses it."
    )
    updated_code: str = Field(
        ..., description="The ENTIRE completely rewritten file with the fix applied. Do not use markdown code blocks."
    )


def generate_patch(current_code: str, error_output: str) -> AgentPatch:
    """Generate a structured patch from source code and an error trace.

    Args:
        current_code: The current source code that failed.
        error_output: The pytest stack trace or failure output.

    Returns:
        A structured patch model containing the reasoning and updated code.

    Raises:
        RuntimeError: If the Gemini request fails or the response does not parse.
    """

    contents = (
        "Current code:\n"
        "```python\n"
        f"{current_code}\n"
        "```\n\n"
        "Error output:\n"
        "```text\n"
        f"{error_output}\n"
        "```"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_MESSAGE,
                response_mime_type="application/json",
                response_schema=AgentPatch,
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini patch request failed: {exc}") from exc

    patch = response.parsed
    if patch is None:
        raise RuntimeError("Gemini returned no parsed structured output.")

    return patch


def apply_patch(filepath: str, patch: AgentPatch) -> None:
    """Safely overwrite a file with the provided patch.

    Args:
        filepath: Path to the file that should be overwritten.
        patch: Parsed patch data containing the updated file contents.

    Raises:
        RuntimeError: If the target path is invalid or cannot be written.
    """

    target_path = Path(filepath)
    if target_path.exists() and not target_path.is_file():
        raise RuntimeError(f"Target path is not a file: {filepath}")

    if target_path.parent and not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold cyan]🛠️ Applying patch to[/bold cyan] [white]{filepath}[/white]...")
    console.print(f"[bold magenta]🧠 Thought Process:[/bold magenta] {patch.thought_process}")

    try:
        target_path.write_text(patch.updated_code, encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Failed to write patch to {filepath}: {exc}") from exc


if __name__ == "__main__":
    demo_path = Path("bad_math.py")
    demo_path.write_text(
        "def divide(a, b):\n    return a /\n\nprint(divide(4, 2))\n",
        encoding="utf-8",
    )

    broken_code = demo_path.read_text(encoding="utf-8")
    fake_error_output = (
        "Traceback (most recent call last):\n"
        '  File "bad_math.py", line 2, in <module>\n'
        "    return a /\n"
        "SyntaxError: invalid syntax\n"
    )

    try:
        patch = generate_patch(broken_code, fake_error_output)
        apply_patch(str(demo_path), patch)
    except RuntimeError as exc:
        console.print(f"[bold red]{exc}[/bold red]")