"""Autonomous repair loop for the self-debugging code agent."""

from __future__ import annotations

from pathlib import Path
from typing import Final
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel

from patcher import apply_patch, generate_patch
from sandbox import run_tests

console: Final[Console] = Console()


def run_agent(target_dir: str, test_command: str, target_file: str, max_iterations: int = 5) -> None:
    """Run the autonomous repair loop until tests pass or iteration budget is exhausted.

    Args:
        target_dir: Directory containing the broken project to repair.
        test_command: Shell command used to run the test suite.
        target_file: File that should be patched on each failed iteration.
        max_iterations: Maximum number of repair attempts before giving up.

    Raises:
        RuntimeError: If the target file cannot be read.
    """

    target_path = Path(target_file)
    iteration = 1

    while iteration <= max_iterations:
        console.print(
            f"[bold cyan]Iteration {iteration}/{max_iterations}[/bold cyan] running [white]{test_command}[/white] in [white]{target_dir}[/white]"
        )
        result = run_tests(target_dir=target_dir, test_command=test_command)

        success = bool(result.get("success", False))
        stdout = str(result.get("stdout", ""))
        stderr = str(result.get("stderr", ""))

        console.print(
            Panel.fit(
                f"[bold]Success:[/bold] {success}\n"
                f"[bold]Stdout:[/bold]\n{stdout or '[dim]No stdout[/dim]'}\n\n"
                f"[bold]Stderr:[/bold]\n{stderr or '[dim]No stderr[/dim]'}",
                title=f"Iteration {iteration}",
                border_style="green" if success else "red",
            )
        )

        if success:
            console.print(
                Panel.fit(
                    "[bold green]TEST SUITE PASSED[/bold green]",
                    border_style="green",
                    title="Victory",
                )
            )
            break

        if not target_path.exists() or not target_path.is_file():
            raise RuntimeError(f"Target file does not exist or is not a file: {target_file}")

        current_code = target_path.read_text(encoding="utf-8")
        error_output = stderr if stderr.strip() else stdout

        patch = generate_patch(current_code=current_code, error_output=error_output)
        apply_patch(filepath=str(target_path), patch=patch)

        iteration += 1

    else:
        console.print(
            Panel.fit(
                "[bold red]MAX ITERATIONS REACHED WITHOUT A PASS[/bold red]",
                border_style="red",
                title="Failure",
            )
        )


if __name__ == "__main__":
    demo_root = Path("demo_project")
    demo_root.mkdir(parents=True, exist_ok=True)

    demo_target_file = demo_root / "broken_math.py"
    demo_target_file.write_text(
        "def add(a, b):\n    return a - b\n\n\nif __name__ == '__main__':\n    print(add(2, 1))\n",
        encoding="utf-8",
    )

    demo_tests = demo_root / "test_broken_math.py"
    demo_tests.write_text(
        "from broken_math import add\n\n\ndef test_add():\n    assert add(2, 1) == 3\n",
        encoding="utf-8",
    )

    run_agent(
        target_dir="./mock_project",
        test_command="pytest test_calculator.py",
        target_file="./mock_project/calculator.py",
        max_iterations=3,
    )