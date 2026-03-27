"""
Split a repository into directory-level modules.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List


IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


EXTENSIONS = {
    ".py": "python",
    ".md": "markdown",
    ".json": "json",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
}


@dataclass
class ModuleChunk:
    name: str
    path: str
    language: str
    full_content: str
    source_files: list[str]


# ----------------------------------------
# helpers
# ----------------------------------------


def get_language(files: List[Path]) -> str:

    counts = {}

    for f in files:

        lang = EXTENSIONS.get(f.suffix)

        if not lang:
            continue

        counts[lang] = counts.get(lang, 0) + 1

    if not counts:
        return "unknown"

    return max(counts, key=counts.get)


def concat_files(
    files: List[Path],
    root: Path,
) -> str:

    parts = []

    for f in sorted(files):

        try:
            text = read_text_file(f)

        except Exception:
            continue

        rel = f.relative_to(root)

        parts.append(
            f"=== {rel} ===\n{text}"
        )

    return "\n\n".join(parts)


def read_text_file(file_path: Path) -> str:
    raw = file_path.read_bytes()

    if not raw:
        return ""

    # Common case for UTF-16 files that appear as alternating NULL bytes when
    # decoded as UTF-8.
    if raw.count(b"\x00") > max(4, len(raw) // 10):
        for encoding in ("utf-16", "utf-16-le", "utf-16-be"):
            try:
                return sanitize_text(raw.decode(encoding))
            except UnicodeDecodeError:
                continue

    return sanitize_text(raw.decode("utf-8", errors="ignore"))


def sanitize_text(text: str) -> str:
    return text.replace("\x00", "")


def iter_module_directories(root: Path) -> List[Path]:
    directories = [root]

    for path in root.rglob("*"):

        if not path.is_dir():
            continue

        rel = path.relative_to(root)

        if any(part in IGNORE_DIRS for part in rel.parts):
            continue

        directories.append(path)

    return directories


# ----------------------------------------
# main
# ----------------------------------------


def chunk_repository(
    repo_path: str,
) -> List[ModuleChunk]:

    root = Path(repo_path)

    modules = []

    for d in iter_module_directories(root):

        rel = d.relative_to(root)

        files = [
            f
            for f in d.iterdir()
            if f.is_file()
            and f.suffix in EXTENSIONS
        ]

        if not files:
            continue

        full = concat_files(
            files,
            root,
        )

        if not full:
            continue

        module_path = str(rel) if rel.parts else "."
        module_name = ".".join(rel.parts) if rel.parts else root.name

        modules.append(
            ModuleChunk(
                name=module_name,
                path=module_path,
                language=get_language(files),
                full_content=full,
                source_files=[
                    str(file.relative_to(root))
                    for file in sorted(files)
                ],
            )
        )

    return modules
