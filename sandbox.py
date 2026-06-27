"""Execution sandbox utilities for running test commands safely."""

from __future__ import annotations

import os
import signal
import subprocess
from typing import Any


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Terminate a process group, then force kill if it stays alive."""

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        process.terminate()

    try:
        process.wait(timeout=1)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError:
        process.kill()

    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def run_tests(target_dir: str, test_command: str, timeout: int = 10) -> dict[str, Any]:
    """Run a test command in a target directory and capture the result."""

    environment = os.environ.copy()

    try:
        process = subprocess.Popen(
            test_command,
            cwd=target_dir,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            start_new_session=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.output or ""
            stderr = exc.stderr or ""
            _terminate_process_group(process)
            try:
                more_stdout, more_stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                more_stdout, more_stderr = "", ""
            stdout = (stdout or "") + (more_stdout or "")
            stderr = (stderr or "") + (more_stderr or "")
            timeout_message = f"Timeout Error: test command exceeded {timeout} seconds."
            if stderr:
                stderr = f"{stderr.rstrip()}\n{timeout_message}\n"
            else:
                stderr = f"{timeout_message}\n"
            return {"success": False, "stdout": stdout, "stderr": stderr}

        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
        }
    except FileNotFoundError as exc:
        return {"success": False, "stdout": "", "stderr": str(exc)}
    except OSError as exc:
        return {"success": False, "stdout": "", "stderr": str(exc)}
