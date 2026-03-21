"""
Module Chunker
--------------
One module = one directory.

For every directory that contains source files, we:
  1. Collect all supported source files in that directory (non-recursive —
     sub-directories become their own modules)
  2. Concatenate their contents with a clear file header between each
  3. Return one ModuleChunk per directory

The full concatenated content is what gets embedded (nomic handles 8192 tokens)
and stored as modules.full_content.

Directory structure example:
  src/
    auth/          → module "src.auth"   (auth files only, not sub-dirs)
      service.py
      models.py
    api/           → module "src.api"
      routes.py
    main.py        → module "src"        (root-level files of src/)
  tests/           → module "tests"
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Directories to never descend into
IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".next", ".mypy_cache", "coverage", ".tox",
    ".eggs", "*.egg-info",
}

# Supported source file extensions → language label
SUPPORTED_EXTENSIONS = {
    ".py":   "python",
    ".js":   "javascript",
    ".jsx":  "javascript",
    ".ts":   "typescript",
    ".tsx":  "typescript",
    ".java": "java",
    ".go":   "go",
    ".rs":   "rust",
    ".rb":   "ruby",
    ".php":  "php",
    ".cs":   "csharp",
    ".cpp":  "cpp",
    ".c":    "c",
    ".kt":   "kotlin",
    ".swift":"swift",
}

# Hard cap on full_content stored in DB — nomic handles 8192 tokens (~32k chars).
# We cap a bit below that to stay safe with the LLM context too.
MAX_CONTENT_CHARS = 28_000


@dataclass
class ModuleChunk:
    """
    Everything about one module (one directory) needed by the pipeline.

    name         : dot-separated module path,  e.g.  "src.auth"
    path         : slash-separated directory,  e.g.  "src/auth"
    language     : dominant language (most files)
    full_content : all source files concatenated with === filename === headers
    """
    name:         str
    path:         str
    language:     str
    full_content: str


def _dominant_language(files: List[Path]) -> str:
    """Return the language that appears most among the given files."""
    counts: dict[str, int] = {}
    for f in files:
        lang = SUPPORTED_EXTENSIONS.get(f.suffix.lower(), "")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return max(counts, key=counts.get) if counts else "unknown"


def _concat_files(files: List[Path], repo_root: Path) -> str:
    """
    Concatenate source files into one string with a header per file.

    Format:
        === path/to/file.py ===
        <file content>

        === path/to/other.py ===
        <file content>
    """
    parts: List[str] = []
    for filepath in sorted(files):
        rel = filepath.relative_to(repo_root)
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if content:
            parts.append(f"=== {rel} ===\n{content}")

    full = "\n\n".join(parts)
    # Truncate if the module is extremely large
    if len(full) > MAX_CONTENT_CHARS:
        full = full[:MAX_CONTENT_CHARS] + "\n\n... [truncated: content exceeds embedding limit]"
    return full


def chunk_repository(repo_path: str) -> List[ModuleChunk]:
    """
    Walk the repository and return one ModuleChunk per directory.

    Only looks at source files directly inside each directory
    (not recursive — sub-directories are their own modules).
    Directories with no supported source files are skipped.

    Args:
        repo_path: Absolute path to the cloned repository.

    Returns:
        List[ModuleChunk] ready for embedding and storage.
    """
    repo_root = Path(repo_path)
    modules:   List[ModuleChunk] = []

    for directory in sorted(repo_root.rglob("*")):
        if not directory.is_dir():
            continue

        # Skip ignored directories
        relative_dir = directory.relative_to(repo_root)
        if any(part in IGNORE_DIRS for part in relative_dir.parts):
            continue

        # Collect source files directly in this directory (non-recursive)
        source_files = [
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not source_files:
            continue

        # Build the module name and path
        rel_path    = str(relative_dir)                            # e.g. "src/auth"
        module_name = rel_path.replace("/", ".").replace("\\", ".") # e.g. "src.auth"

        full_content = _concat_files(source_files, repo_root)
        if not full_content.strip():
            continue

        modules.append(ModuleChunk(
            name         = module_name,
            path         = rel_path,
            language     = _dominant_language(source_files),
            full_content = full_content,
        ))

    # Also handle source files sitting directly at repo root
    root_files = [
        f for f in repo_root.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if root_files:
        full_content = _concat_files(root_files, repo_root)
        if full_content.strip():
            modules.insert(0, ModuleChunk(
                name         = "root",
                path         = ".",
                language     = _dominant_language(root_files),
                full_content = full_content,
            ))

    return modules