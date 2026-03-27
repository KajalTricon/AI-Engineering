#!/usr/bin/env python3
"""
One-command project setup for CodebaseDocumentor.

This script:
- creates the backend virtual environment if needed
- installs backend Python dependencies
- creates frontend/backend env files from examples when missing
- installs frontend npm dependencies when Node.js is available

Run from the CodebaseDocumentor root:
    python3 setup.py

Helpful run commands after setup:

    # Terminal 1
    # cd backend
    # ./docai/bin/python3 -m uvicorn app.main:app --reload --port 8000

    # Terminal 2
    # cd frontend
    # npm run dev
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_VENV_DIR = BACKEND_DIR / "docai"


def info(message: str) -> None:
    print(f"[setup] {message}")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"[setup] ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def run(command: list[str], *, cwd: Path | None = None) -> None:
    location = str(cwd or ROOT)
    info(f"Running in {location}: {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        fail("Python 3.10 or newer is required.")


def ensure_backend_venv() -> Path:
    if not BACKEND_VENV_DIR.exists():
        info("Creating backend virtual environment...")
        venv.EnvBuilder(with_pip=True).create(BACKEND_VENV_DIR)

    if os.name == "nt":
        python_path = BACKEND_VENV_DIR / "Scripts" / "python.exe"
    else:
        python_path = BACKEND_VENV_DIR / "bin" / "python3"
        if not python_path.exists():
            python_path = BACKEND_VENV_DIR / "bin" / "python"

    if not python_path.exists():
        fail("Backend virtual environment was created, but Python was not found inside it.")

    return python_path


def ensure_env_file(example_path: Path, target_path: Path) -> None:
    if target_path.exists():
        info(f"Keeping existing env file: {target_path.relative_to(ROOT)}")
        return

    if not example_path.exists():
        fail(f"Missing env template: {example_path.relative_to(ROOT)}")

    shutil.copyfile(example_path, target_path)
    info(f"Created {target_path.relative_to(ROOT)} from template")


def install_backend(python_path: Path) -> None:
    requirements_path = BACKEND_DIR / "requirements.txt"
    if not requirements_path.exists():
        fail("backend/requirements.txt was not found.")

    run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], cwd=BACKEND_DIR)
    run([str(python_path), "-m", "pip", "install", "-r", str(requirements_path)], cwd=BACKEND_DIR)


def install_frontend() -> None:
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")

    if not node_path or not npm_path:
        info("Node.js/npm not found. Skipping frontend dependency installation.")
        info("Install Node.js 20+ and rerun setup.py to complete frontend setup.")
        return

    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        fail("frontend/package.json was not found.")

    run([npm_path, "install"], cwd=FRONTEND_DIR)


def print_next_steps(python_path: Path) -> None:
    backend_run = f"{python_path} -m uvicorn app.main:app --reload --port 8000"
    message = f"""
    Setup complete.

    Next steps:

    1. Fill in backend/.env with your actual database and Gemini values if needed.
    2. Start the backend:
       cd "{BACKEND_DIR}"
       {backend_run}

    3. Start the frontend:
       cd "{FRONTEND_DIR}"
       npm run dev

    4. Open:
       http://localhost:5173
    """
    print(textwrap.dedent(message).strip())


def main() -> None:
    ensure_python()

    if not BACKEND_DIR.exists():
        fail("backend directory not found. Run this script from CodebaseDocumentor root.")
    if not FRONTEND_DIR.exists():
        fail("frontend directory not found.")

    backend_python = ensure_backend_venv()

    ensure_env_file(BACKEND_DIR / ".env.example", BACKEND_DIR / ".env")
    ensure_env_file(FRONTEND_DIR / ".env.example", FRONTEND_DIR / ".env")

    install_backend(backend_python)
    install_frontend()
    print_next_steps(backend_python)


if __name__ == "__main__":
    main()
