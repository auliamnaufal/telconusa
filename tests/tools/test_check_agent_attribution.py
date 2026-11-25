import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "check_agent_attribution.py"
HUMAN_ENV = {
    "GIT_AUTHOR_NAME": "Jane Doe",
    "GIT_AUTHOR_EMAIL": "jane@example.com",
    "GIT_COMMITTER_NAME": "Jane Doe",
    "GIT_COMMITTER_EMAIL": "jane@example.com",
}

FLAGGED_TEXT = [
    "feat: add catalog\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
    "fix: bug\n\nCo-authored-by: Copilot <copilot@users.noreply.github.com>",
    "fix: bug\n\nAssisted-by: ChatGPT",
    "fix: bug\n\nSigned-off-by: Codex <codex@openai.com>",
    "feat: x\n\nGenerated with Claude Code",
    "feat: x\n\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)",
    "feat: x\n\nCreated with Codex",
]

CLEAN_TEXT = [
    "fix: use a server-side cursor for pagination\n\nThe cursor avoids loading every row.",
    "feat: add gemini-free pricing page\n\nCo-authored-by: Jane Doe <jane@example.com>",
    "docs: explain agent roles\n\nSigned-off-by: John Roe <john@example.com>",
]


@pytest.mark.parametrize("text", FLAGGED_TEXT)
def test_flags_agent_attribution(attribution: Any, text: str) -> None:
    errors = attribution.check_text("msg", text)
    assert errors and errors[0].startswith("ERROR: msg: line ")


@pytest.mark.parametrize("text", CLEAN_TEXT)
def test_passes_human_messages(attribution: Any, text: str) -> None:
    assert attribution.check_text("msg", text) == []


@pytest.mark.parametrize(
    ("name", "email", "flagged"),
    [
        ("Codex", "codex@example.com", True),
        ("Jane Doe", "noreply@anthropic.com", True),
        ("Amazon Q Developer", "q@example.com", True),
        ("copilot-swe-agent[bot]", "bot@example.com", True),
        ("Jane Doe", "jane@example.com", False),
        ("dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com", False),
    ],
)
def test_identity(attribution: Any, name: str, email: str, flagged: bool) -> None:
    assert bool(attribution.check_identity("author", name, email)) is flagged


def run_cli(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd, env={**os.environ, **HUMAN_ENV, **(env or {})},
    )


def test_message_file_cli(tmp_path: Path) -> None:
    good = tmp_path / "good"
    good.write_text("fix: tune cursor batch size\n\n# Please enter the commit message\n", encoding="utf-8")
    assert run_cli("--message-file", str(good), cwd=tmp_path).returncode == 0

    bad = tmp_path / "bad"
    bad.write_text("feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n", encoding="utf-8")
    result = run_cli("--message-file", str(bad), cwd=tmp_path)
    assert result.returncode == 1
    assert "ERROR: commit message" in result.stdout
    assert "No coding agent attribution" in result.stdout


def test_message_file_with_agent_git_identity(tmp_path: Path) -> None:
    message = tmp_path / "msg"
    message.write_text("fix: ok\n", encoding="utf-8")
    result = run_cli("--message-file", str(message), env={"GIT_AUTHOR_NAME": "Codex"}, cwd=tmp_path)
    assert result.returncode == 1
    assert "belongs to a coding agent" in result.stdout


def test_text_env_cli(tmp_path: Path) -> None:
    clean = run_cli("--text-env", "PR_TITLE", "--text-env", "PR_BODY", env={"PR_TITLE": "Add cursor paging", "PR_BODY": "Closes #1"})
    assert clean.returncode == 0
    dirty = run_cli("--text-env", "PR_BODY", env={"PR_BODY": "Summary\n\nGenerated with Claude Code"})
    assert dirty.returncode == 1
    assert "env PR_BODY" in dirty.stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_range_checks_author_committer_and_body(tmp_path: Path, attribution: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    def git(*args: str, env: dict[str, str] | None = None) -> None:
        subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=tmp_path, check=True, capture_output=True, env={**os.environ, **HUMAN_ENV, **(env or {})})

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "base")
    git("commit", "-q", "--allow-empty", "-m", "feat: human work\n\nUses a cursor.")
    git("commit", "-q", "--allow-empty", "-m", "feat: agent work", env={"GIT_AUTHOR_NAME": "Codex"})
    git("commit", "-q", "--allow-empty", "-m", "feat: more\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    monkeypatch.chdir(tmp_path)

    assert attribution.check_range("HEAD~3..HEAD~2") == []
    errors = attribution.check_range("HEAD~3..HEAD")
    assert len(errors) == 2
    assert any("author" in e and "Codex" in e for e in errors)
    assert any("Co-Authored-By" in e or "co-authored-by" in e for e in errors)
