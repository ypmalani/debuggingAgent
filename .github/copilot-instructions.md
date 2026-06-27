# Project Context: Self-Debugging Code Agent

## 🎯 Project Overview
We are building a fully autonomous Self-Debugging Code Agent. The goal of this agent is to take a broken Python codebase and its test suite, run the tests, parse the errors, write patches via an LLM, re-run the tests, and iterate autonomously until the test suite passes (green). No human-in-the-loop is required during the loop.

## 🛠️ Tech Stack & Tooling
- **Agent Language:** Python 3.11+
- **Target Codebase Language:** Python
- **Testing Framework:** `pytest` (used by the sandbox to evaluate target code)
- **LLM Integration:** Official `openai` or `anthropic` Python SDKs
- **Structured Output:** `pydantic` (for defining rigid JSON schemas for LLM responses)
- **CLI/Logging:** `rich` (for beautiful, readable console output detailing the agent's inner monologue)

## 🏗️ Architecture & Milestones
The project is strictly divided into 5 iterative milestones. Copilot should assist in building these sequentially, ensuring each layer is robust before moving to the next:
1. **Execution Sandbox (`sandbox.py`):** Subprocess wrapper to execute `pytest` in a target directory, capturing `stdout`/`stderr`, exit codes, and handling infinite loop timeouts.
2. **LLM Analyzer (`brain.py`):** The LLM client setup. Takes broken code and stack traces and outputs diagnostic reasoning.
3. **Structured Patcher (`patcher.py`):** Forces the LLM to output valid JSON (using Pydantic schemas) containing the `thought_process` and the `updated_code`. Handles safe file overwriting.
4. **Autonomous Loop (`agent.py`):** The main `while` loop tying the sandbox, brain, and patcher together. Stops when tests pass or `max_iterations` is reached.
5. **Context & Memory (`memory.py`):** A system to track failed attempts and inject them into the prompt so the LLM does not repeat the same mistakes.

## 📜 Coding Standards & Rules for Copilot

### 1. Python Best Practices
- **Strict Typing:** ALL functions must have type hints. Use explicit return types.
- **Docstrings:** Use Google-style docstrings for all modules, classes, and functions.
- **Error Handling:** Do not use bare `except:` clauses. Catch specific exceptions (e.g., `subprocess.TimeoutExpired`, `json.JSONDecodeError`).

### 2. LLM / Agentic Patterns
- **No Markdown in JSON:** When prompting the LLM for code, enforce strict JSON schemas. Do not allow the LLM to wrap JSON in ```json markdown blocks. 
- **Idempotency:** File editing operations must be idempotent and safe. Always verify file paths before overwriting.
- **Context Limits:** Keep in mind that passing entire codebases to the LLM might exceed token limits. Focus on passing the *specific broken file* and the *specific test error*.

### 3. Subprocess Safety
- Always use `subprocess.run` with `capture_output=True`, `text=True`, and a strict `timeout` parameter to prevent the agent from hanging indefinitely on infinite loops written by the AI.

### 4. Communication Style
- When answering queries, be concise. Skip pleasantries.
- Provide the exact code to modify, clearly indicating file paths.
- If an architectural decision violates these instructions, flag it immediately.