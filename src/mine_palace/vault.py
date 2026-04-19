from __future__ import annotations

import itertools
import re
from collections import defaultdict
from pathlib import Path

from .models import VaultNote

HEADING_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z][\w/-]+)")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
HIDDEN_PARTS = {".git", ".obsidian", ".github", "__pycache__", ".claude", ".vim"}


def parse_vault(
    vault_dir: Path,
    *,
    limit: int | None = None,
    include_districts: list[str] | None = None,
) -> list[VaultNote]:
    notes: list[VaultNote] = []

    include_set = {item.lower() for item in include_districts or []}
    for path in sorted(vault_dir.rglob("*.md")):
        if _should_skip(path, vault_dir):
            continue

        district = _district_name(path, vault_dir)
        if include_set and district.lower() not in include_set:
            continue

        note = _parse_note(path, vault_dir, district)
        if note is not None:
            notes.append(note)

    if limit is not None and len(notes) > limit:
        notes = _balanced_limit(notes, limit)

    return notes


def _should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part.startswith(".") or part in HIDDEN_PARTS for part in rel.parts):
        return True
    return False


def _district_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    if len(rel.parts) == 1:
        return "Vault"
    return rel.parts[0]


def _parse_note(path: Path, root: Path, district: str) -> VaultNote | None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = FRONTMATTER_RE.sub("", raw).strip()
    if not text:
        return None

    title = _extract_title(text, path)
    excerpt = _extract_excerpt(text)
    slug = path.relative_to(root).with_suffix("").as_posix().replace("/", "--").lower()
    links = sorted(set(_clean_tokens(WIKILINK_RE.findall(text))))
    tags = sorted(set(TAG_RE.findall(text)))

    return VaultNote(
        slug=slug,
        title=title,
        path=path.relative_to(root),
        district=district,
        content=text,
        excerpt=excerpt,
        links=links,
        tags=tags,
    )


def _extract_title(text: str, path: Path) -> str:
    match = HEADING_RE.search(text)
    if match:
        return match.group(1).strip()
    return path.stem.replace("-", " ").replace("_", " ").strip().title()


def _extract_excerpt(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("---"):
            continue
        if stripped.startswith("- [") or stripped.startswith("- "):
            continue
        return _truncate_whitespace(stripped, 72)
    return "No preview text available"


def _clean_tokens(values: list[str]) -> list[str]:
    cleaned = []
    for value in values:
        token = value.strip()
        if token:
            cleaned.append(token)
    return cleaned


def _balanced_limit(notes: list[VaultNote], limit: int) -> list[VaultNote]:
    grouped: dict[str, list[VaultNote]] = defaultdict(list)
    for note in notes:
        grouped[note.district].append(note)

    for items in grouped.values():
        items.sort(key=lambda note: note.path.as_posix())

    ordered_districts = sorted(
        grouped,
        key=lambda district: (-len(grouped[district]), district.lower()),
    )
    iterators = [iter(grouped[district]) for district in ordered_districts]

    selected: list[VaultNote] = []
    while len(selected) < limit and iterators:
        next_iterators = []
        for iterator in iterators:
            note = next(iterator, None)
            if note is None:
                continue
            selected.append(note)
            if len(selected) == limit:
                break
            next_iterators.append(iterator)
        iterators = next_iterators

    return selected


def _truncate_whitespace(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"
