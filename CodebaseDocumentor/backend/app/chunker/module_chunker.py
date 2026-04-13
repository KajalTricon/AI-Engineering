"""
Split repositories into directory-level modules with repository-aware metadata.
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
    ".vscode",
    ".gitignore",
    ".git-ignore",
    ".idea",
    ".next",
    ".turbo",
    ".pytest_cache",
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
    ".ipynb": "jupyter",
    ".sh": "shell",
}


@dataclass
class ModuleChunk:
    repository_name: str
    name: str
    path: str
    language: str
    full_content: str
    source_files: list[str]


def get_language(files: List[Path]) -> str:
    counts: dict[str, int] = {}
    for file_path in files:
        language = EXTENSIONS.get(file_path.suffix)
        if language:
            counts[language] = counts.get(language, 0) + 1
    return max(counts, key=counts.get) if counts else "unknown"


def sanitize_text(text: str) -> str:
    return text.replace("\x00", "")


def read_text_file(file_path: Path) -> str:
    raw = file_path.read_bytes()
    if not raw:
        return ""

    if raw.count(b"\x00") > max(4, len(raw) // 10):
        for encoding in ("utf-16", "utf-16-le", "utf-16-be"):
            try:
                return sanitize_text(raw.decode(encoding))
            except UnicodeDecodeError:
                continue

    return sanitize_text(raw.decode("utf-8", errors="ignore"))


def concat_files(files: List[Path], root: Path, repository_name: str) -> str:
    parts: list[str] = []
    for file_path in sorted(files):
        try:
            text = read_text_file(file_path)
        except Exception:
            continue

        rel = file_path.relative_to(root)
        parts.append(f"=== {repository_name}/{rel} ===\n{text}")

    return "\n\n".join(parts)


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


def chunk_repository(repo_path: str, repository_name: str) -> List[ModuleChunk]:
    root = Path(repo_path)
    modules: list[ModuleChunk] = []

    for directory in iter_module_directories(root):
        rel = directory.relative_to(root)
        files = [
            file_path
            for file_path in directory.iterdir()
            if file_path.is_file() and file_path.suffix in EXTENSIONS
        ]

        if not files:
            continue

        full_content = concat_files(files, root, repository_name)
        if not full_content:
            continue

        module_path = str(rel) if rel.parts else "."
        module_name = ".".join(rel.parts) if rel.parts else repository_name

        modules.append(
            ModuleChunk(
                repository_name=repository_name,
                name=module_name,
                path=module_path,
                language=get_language(files),
                full_content=full_content,
                source_files=[str(file_path.relative_to(root)) for file_path in sorted(files)],
            )
        )

    return modules
