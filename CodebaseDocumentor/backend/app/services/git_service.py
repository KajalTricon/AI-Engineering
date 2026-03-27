"""
Git and repository identity helpers.
"""

import asyncio
from urllib.parse import urlparse


def normalize_github_url(github_url: str) -> str:
    raw = github_url.strip()

    if raw.startswith("git@github.com:"):
        raw = raw.replace("git@github.com:", "https://github.com/", 1)

    parsed = urlparse(raw)
    host = parsed.netloc.lower() or "github.com"

    if "github.com" not in host:
        raise ValueError("Only GitHub repository URLs are supported.")

    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]

    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub repository URL must include owner and repository name.")

    owner, repo = parts[0], parts[1]
    return f"https://github.com/{owner}/{repo}"


async def get_remote_head_commit(github_url: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "git",
        "ls-remote",
        github_url,
        "HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"git ls-remote failed: {stderr.decode().strip()}")

    line = stdout.decode().strip().splitlines()
    if not line:
        raise RuntimeError("No remote HEAD commit found.")

    return line[0].split()[0]


async def get_local_head_commit(repo_path: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        repo_path,
        "rev-parse",
        "HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {stderr.decode().strip()}")

    return stdout.decode().strip()
