#!/usr/bin/env python3
"""Enforce the rule that no coding agent is author, co-author or contributor.

Modes (combinable):
  --message-file PATH   one commit message (commit-msg hook); also checks the
                        configured git author/committer identity
  --range A..B          every commit in a git range (author, committer, message)
  --text-env VAR        text from an environment variable, e.g. a PR title or body

Repository files are never scanned.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

AGENT_NAMES = (
    "claude", "anthropic", "codex", "openai", "chatgpt", "copilot", "cursor", "gemini",
    "windsurf", "devin", "aider", "cline", "tabnine", "amazon q", "codewhisperer",
)
AGENT = r"(?<![A-Za-z0-9])(?:" + "|".join(n.replace(" ", r"[\s_-]?") for n in AGENT_NAMES) + r")(?![A-Za-z0-9])"
AGENT_RE = re.compile(AGENT, re.IGNORECASE)

TRAILER_RE = re.compile(
    r"^\s*(?P<key>co-authored-by|generated-by|assisted-by|signed-off-by|reviewed-by|authored-by|created-by)"
    r"\s*:\s*(?P<value>.*)$",
    re.IGNORECASE,
)
GENERATED_RE = re.compile(
    r"\b(?:generated|created|authored|written|built|made|assisted|powered|co-authored)\s+(?:with|by|using)\s+"
    r"\W*(?:(?:the|help\s+of|assistance\s+of)\s+)?" + AGENT,
    re.IGNORECASE,
)
ROBOT_EMOJI = "\U0001F916"
SCISSORS = "# ------------------------ >8 ------------------------"
IDENT_RE = re.compile(r"^(?P<name>.*?)\s*<(?P<email>[^>]*)>")
RULE_POINTER = "See AGENTS.md rule 'No coding agent attribution'."


def check_text(where: str, text: str) -> list[str]:
    errors: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        trailer = TRAILER_RE.match(line)
        if trailer and AGENT_RE.search(trailer["value"]):
            errors.append(f"ERROR: {where}: line {number}: {trailer['key']} trailer names a coding agent: {line.strip()!r}")
        elif GENERATED_RE.search(line) or (ROBOT_EMOJI in line and AGENT_RE.search(line)):
            errors.append(f"ERROR: {where}: line {number}: attribution line names a coding agent: {line.strip()!r}")
    return errors


def check_identity(where: str, name: str, email: str) -> list[str]:
    if AGENT_RE.search(name) or AGENT_RE.search(email):
        return [f"ERROR: {where}: identity {name} <{email}> belongs to a coding agent"]
    return []


def check_configured_identity() -> list[str]:
    errors: list[str] = []
    for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        try:
            out = subprocess.run(["git", "var", var], capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            continue
        match = IDENT_RE.match(out.strip())
        if match:
            errors += check_identity(f"git {var.split('_')[1].lower()}", match["name"], match["email"])
    return errors


def read_commit_message(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    kept: list[str] = []
    for line in text.splitlines():
        if line.startswith(SCISSORS):
            break
        if not line.startswith("#"):
            kept.append(line)
    return "\n".join(kept)


def check_range(rev_range: str) -> list[str]:
    fmt = "%x1e%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B"
    try:
        out = subprocess.run(
            ["git", "log", "--no-merges", f"--format={fmt}", rev_range],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or exc
        return [f"ERROR: --range {rev_range}: git log failed: {str(detail).strip()}"]
    errors: list[str] = []
    for record in filter(None, out.split("\x1e")):
        sha, author, author_email, committer, committer_email, message = record.lstrip("\n").split("\x1f", 5)
        where = f"commit {sha[:8]}"
        errors += check_identity(f"{where} author", author, author_email)
        errors += check_identity(f"{where} committer", committer, committer_email)
        errors += check_text(f"{where} message", message)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--message-file", type=Path, help="commit message file (commit-msg hook)")
    parser.add_argument("--range", dest="rev_range", help="git revision range, e.g. origin/main..HEAD")
    parser.add_argument("--text-env", action="append", default=[], metavar="VAR", help="environment variable holding text to check")
    args = parser.parse_args(argv)
    if not (args.message_file or args.rev_range or args.text_env):
        parser.error("give at least one of --message-file, --range, --text-env")

    errors: list[str] = []
    if args.message_file:
        errors += check_text(f"commit message {args.message_file}", read_commit_message(args.message_file))
        errors += check_configured_identity()
    if args.rev_range:
        errors += check_range(args.rev_range)
    for var in args.text_env:
        errors += check_text(f"env {var}", os.environ.get(var, ""))

    for line in errors:
        print(line)
    if errors:
        print(RULE_POINTER)
        return 1
    print("OK: no coding agent attribution found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
