"""
Git utilities
"""

import asyncio
from pathlib import Path

from app.core.settings import settings


async def clone_repo(
    github_url: str,
    repo_id: str,
) -> str:
    """
    Clone repo to /tmp/repos/{repo_id}
    """

    clone_dir = Path(settings.CLONE_BASE_DIR) / repo_id

    clone_dir.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    proc = await asyncio.create_subprocess_exec(
        "git",
        "clone",
        "--depth=1",
        github_url,
        str(clone_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, err = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"git clone failed: {err.decode()}"
        )

    return str(clone_dir)