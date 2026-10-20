#!/usr/bin/env python3
"""Audit environment variables referenced in source code."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv",
    "__pycache__", "dist", "build", ".tox", ".mypy_cache",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".sh", ".bash", ".yml", ".yaml", ".toml", ".json",
}

PATTERNS = [
    re.compile(r'os\.getenv\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'os\.environ\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'process\.env\.([A-Za-z_][A-Za-z0-9_]*)'),
    re.compile(r'process\.env\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'\$\{?([A-Z][A-Z0-9_]*)\}?'),
]


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines from an env-style file."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key and not key.startswith("#"):
            values[key] = ""
    return values


def scan_references(root: Path) -> dict[str, list[str]]:
    """Scan source files and return referenced environment variables."""
    references: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix not in SOURCE_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = path.relative_to(root)
        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                variable = match.group(1)
                line_number = text.count("\n", 0, match.start()) + 1
                references.setdefault(variable, []).append(f"{relative}:{line_number}")
    return references


def build_report(root, references, env_values, example_values):
    referenced = set(references)
    declared = set(env_values)
    example = set(example_values)
    return {
        "root": str(root),
        "referenced_count": len(referenced),
        "env_file_count": len(declared),
        "example_file_count": len(example),
        "missing_from_example": sorted(referenced - example),
        "unused_in_example": sorted(example - referenced),
        "only_in_env_file": sorted(declared - example),
        "missing_from_env_file": sorted(example - declared),
        "references": {key: references[key] for key in sorted(references)},
    }


def render_text(report):
    lines = [
        f"envcensus report for {report['root']}",
        f"referenced variables: {report['referenced_count']}",
        f"variables in env file: {report['env_file_count']}",
        f"variables in example file: {report['example_file_count']}",
        "",
    ]

    def section(title, items):
        lines.append(title)
        if items:
            lines.extend(f"  - {item}" for item in items)
        else:
            lines.append("  (none)")
        lines.append("")

    section("Missing from example file:", report["missing_from_example"])
    section("Declared in example but unused:", report["unused_in_example"])
    section("Only in env file:", report["only_in_env_file"])
    section("Missing from env file:", report["missing_from_env_file"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit environment variable usage.")
    parser.add_argument("path", nargs="?", default=".", help="project root")
    parser.add_argument("--env-file", default=".env", help="environment file")
    parser.add_argument("--example-file", default=".env.example", help="example env file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="exit 1 if variables are missing from the example file",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    references = scan_references(root)
    env_values = parse_env_file(root / args.env_file)
    example_values = parse_env_file(root / args.example_file)
    report = build_report(root, references, env_values, example_values)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.fail_on_missing and report["missing_from_example"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
